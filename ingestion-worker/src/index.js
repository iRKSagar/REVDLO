// Mr. Oldverdict Ingestion Worker
// Subrequest budget: 5 Reddit + 1 Trends + 3 HN + 10 Supabase = 19 total

const SUBREDDITS = {
  A: 'mildlyinfuriating',
  B: 'antiwork',
  C: 'AmItheAsshole',
  D: 'Showerthoughts',
  E: 'Stoicism'
};

const BLACKLIST_KEYWORDS = [
  'trump', 'biden', 'obama', 'modi', 'putin', 'xi', 'sunak', 'labour', 'republican', 'democrat',
  'conservative', 'liberal', 'maga', 'woke', 'israel', 'palestine', 'ukraine', 'russia', 'china',
  'christian', 'muslim', 'islam', 'hindu', 'jewish', 'bible', 'quran', 'torah',
  'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'instagram', 'tiktok', 'twitter', 'netflix',
  'elon', 'musk', 'bezos', 'zuckerberg', 'epstein', 'kardashian',
  'rape', 'suicide', 'murder', 'abuse', 'racist', 'nazi', 'genocide', 'terrorist',
  'porn', 'sex', 'nsfw', 'nude', 'naked', 'death', 'killed', 'shooting', 'war',
  'gen z', 'genz', 'generation z', 'zoomer'
];

// Keyword scoring — boost or penalize based on content performance data
const BOOST_KEYWORDS = [
  // Corporate/work — confirmed strong March 1 2026
  'chief', 'ceo', 'title', 'promotion', 'manager', 'productivity', 'hustle',
  'career', 'office', 'workplace', 'burnout', 'meeting', 'salary', 'corporate',
  'employee', 'professional', 'professionals', 'job', 'hired', 'hiring', 'fired', 'resign', 'boss',
  // AI/tech behavior — confirmed strong March 1 2026
  'ai', 'artificial intelligence', 'algorithm', 'automation', 'robot',
  'chatbot', 'generated', 'digital', 'app', 'subscription',
  // Relatable modern behavior
  'people are', 'everyone is', 'wellness', 'mindfulness', 'optimize',
  'hack', 'routine', 'morning routine', 'millennials'
];

const PENALIZE_KEYWORDS = [
  'wage', 'theft', 'discrimination', 'protest', 'rights', 'lawsuit',
  'arrested', 'crime', 'political', 'election', 'dye', 'lawsuit'
];

function applyKeywordScoring(title, baseScore) {
  const lower = title.toLowerCase();
  let score = baseScore;

  // Boost 2x if any boost keyword found
  if (BOOST_KEYWORDS.some(k => lower.includes(k))) {
    score = score * 2;
  }

  // Penalize 0.5x if any penalize keyword found
  if (PENALIZE_KEYWORDS.some(k => lower.includes(k))) {
    score = score * 0.5;
  }

  return Math.round(score);
}

function passesBlacklist(text) {
  const lower = text.toLowerCase();
  return !BLACKLIST_KEYWORDS.some(word => lower.includes(word));
}

function cleanTitle(title) {
  return title
    .replace(/<[^>]*>/g, '')
    .replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/[^\w\s.,?!'\-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 280);
}

function extractRSSItems(xml) {
  const items = [];
  const itemRegex = /<item[^>]*>([\s\S]*?)<\/item>/gi;
  const titleRegex = /<title[^>]*><!\[CDATA\[([\s\S]*?)\]\]><\/title>|<title[^>]*>([\s\S]*?)<\/title>/i;
  let m;
  while ((m = itemRegex.exec(xml)) !== null) {
    const t = titleRegex.exec(m[1]);
    if (t) {
      const title = cleanTitle(t[1] || t[2] || '');
      if (title.length > 20) items.push(title);
    }
  }
  return items;
}

async function fetchReddit(subreddit, category) {
  try {
    const res = await fetch(`https://www.reddit.com/r/${subreddit}/hot.json?limit=8&t=day`, {
      headers: { 'User-Agent': 'MrOldverdict-Bot/1.0' }
    });
    if (!res.ok) return [];
    const data = await res.json();
    return (data?.data?.children || [])
      .filter(p => !p.data.stickied && !p.data.over_18)
      .map(p => ({
        title: cleanTitle(p.data.title),
        category,
        source: `reddit/r/${subreddit}`,
        engagementScore: applyKeywordScoring(p.data.title, p.data.score + (p.data.num_comments * 3))
      }))
      .filter(p => p.title.length > 20 && passesBlacklist(p.title))
      .slice(0, 3);
  } catch { return []; }
}

async function fetchGoogleTrends() {
  try {
    const res = await fetch('https://trends.google.com/trending/rss?geo=US', {
      headers: { 'User-Agent': 'MrOldverdict-Bot/1.0' }
    });
    if (!res.ok) return [];
    const xml = await res.text();
    return extractRSSItems(xml)
      .filter(passesBlacklist)
      .slice(0, 3)
      .map(title => ({ title, category: 'A', source: 'google_trends_US', engagementScore: applyKeywordScoring(title, 500) }));
  } catch { return []; }
}

async function fetchHackerNews() {
  try {
    const idsRes = await fetch('https://hacker-news.firebaseio.com/v0/topstories.json');
    if (!idsRes.ok) return [];
    const ids = await idsRes.json();
    const stories = await Promise.all(
      ids.slice(0, 2).map(async id => {
        try {
          const res = await fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
          if (!res.ok) return null;
          const item = await res.json();
          if (!item?.title || item.type !== 'story') return null;
          const title = cleanTitle(item.title);
          if (title.length < 20 || !passesBlacklist(title)) return null;
          const cat = title.toLowerCase().match(/work|job|compan|career|hire|fired/) ? 'B' : 'E';
          return { title, category: cat, source: 'hacker_news', engagementScore: applyKeywordScoring(title, (item.score || 0) + ((item.descendants || 0) * 3)) };
        } catch { return null; }
      })
    );
    return stories.filter(Boolean);
  } catch { return []; }
}

async function storeTopic(supabaseUrl, supabaseKey, topic) {
  try {
    const res = await fetch(`${supabaseUrl}/rest/v1/topics`, {
      method: 'POST',
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify({
        raw_topic: topic.title,
        category: topic.category,
        source: topic.source,
        engagement_score: topic.engagementScore,
        blacklist_cleared: true
      })
    });
    return res.ok;
  } catch { return false; }
}

async function runIngestion(env) {
  const results = { fetched: 0, stored: 0, by_source: { reddit: 0, google_trends: 0, hacker_news: 0 }, categories: { A: 0, B: 0, C: 0, D: 0, E: 0 } };
  const allTopics = [];

  // 5 subrequests
  for (const [category, subreddit] of Object.entries(SUBREDDITS)) {
    const topics = await fetchReddit(subreddit, category);
    allTopics.push(...topics);
  }

  // 1 subrequest
  allTopics.push(...await fetchGoogleTrends());

  // 3 subrequests
  allTopics.push(...await fetchHackerNews());

  results.fetched = allTopics.length;

  // Group by category, store top 2 each — max 10 subrequests
  const byCategory = { A: [], B: [], C: [], D: [], E: [] };
  for (const topic of allTopics) {
    if (byCategory[topic.category]) byCategory[topic.category].push(topic);
  }

  for (const [category, topics] of Object.entries(byCategory)) {
    const top2 = topics.sort((a, b) => b.engagementScore - a.engagementScore).slice(0, 2);
    for (const topic of top2) {
      const stored = await storeTopic(env.SUPABASE_URL, env.SUPABASE_KEY, topic);
      if (stored) {
        results.stored++;
        results.categories[category]++;
        if (topic.source.startsWith('reddit')) results.by_source.reddit++;
        else if (topic.source.startsWith('google')) results.by_source.google_trends++;
        else results.by_source.hacker_news++;
      }
    }
  }

  return results;
}

export default {
  async fetch(request, env) {
    if (request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'Ingestion worker standing by.' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });

    const authHeader = request.headers.get('Authorization');
    if (authHeader !== `Bearer ${env.COUNCIL_SECRET}`) return new Response('Unauthorized', { status: 401 });

    try {
      const results = await runIngestion(env);
      return new Response(JSON.stringify({ success: true, message: 'Ingestion complete.', results }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), { status: 500, headers: { 'Content-Type': 'application/json' } });
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      fetch(`https://${env.WORKER_DOMAIN}/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${env.COUNCIL_SECRET}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
    );
  }
};
