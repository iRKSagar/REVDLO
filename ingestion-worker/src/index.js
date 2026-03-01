// Mr. Oldverdict Ingestion Worker
// Sources: Reddit, Google Trends, BBC/Guardian News RSS, Hacker News

const SUBREDDITS = {
  A: ['mildlyinfuriating', 'firstworldproblems'],
  B: ['antiwork', 'LinkedInLunatics'],
  C: ['AmItheAsshole', 'confession'],
  D: ['nosurf', 'Showerthoughts'],
  E: ['Stoicism', 'history']
};

// Google Trends RSS — geo codes for target audience
const TRENDS_FEEDS = [
  { url: 'https://trends.google.com/trending/rss?geo=US', category: 'A' },
  { url: 'https://trends.google.com/trending/rss?geo=GB', category: 'A' },
  { url: 'https://trends.google.com/trending/rss?geo=AU', category: 'D' }
];

// News RSS feeds — BBC and Guardian
const NEWS_FEEDS = [
  { url: 'https://feeds.bbci.co.uk/news/rss.xml', category: 'B' },
  { url: 'https://feeds.bbci.co.uk/news/technology/rss.xml', category: 'B' },
  { url: 'https://www.theguardian.com/society/rss', category: 'C' },
  { url: 'https://www.theguardian.com/money/rss', category: 'E' }
];

const BLACKLIST_KEYWORDS = [
  'trump', 'biden', 'obama', 'modi', 'putin', 'xi', 'sunak', 'labour', 'republican', 'democrat',
  'conservative', 'liberal', 'maga', 'woke', 'israel', 'palestine', 'ukraine', 'russia', 'china',
  'christian', 'muslim', 'islam', 'hindu', 'jewish', 'bible', 'quran', 'torah',
  'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'instagram', 'tiktok', 'twitter', 'netflix',
  'elon', 'musk', 'bezos', 'zuckerberg', 'epstein', 'kardashian',
  'rape', 'suicide', 'murder', 'abuse', 'racist', 'nazi', 'genocide', 'terrorist',
  'porn', 'sex', 'nsfw', 'nude', 'naked',
  'death', 'killed', 'shooting', 'stabbing', 'attack', 'war', 'bombing'
];

function passesBlacklist(text) {
  const lower = text.toLowerCase();
  return !BLACKLIST_KEYWORDS.some(word => lower.includes(word));
}

function cleanTitle(title) {
  return title
    .replace(/<[^>]*>/g, '')         // strip HTML tags
    .replace(/&amp;/g, '&')          // decode common HTML entities
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/[^\w\s.,?!'\-–]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 280);
}

// Extract <title> tags from RSS XML — no DOM parser needed
function extractRSSItems(xml) {
  const items = [];
  const itemRegex = /<item[^>]*>([\s\S]*?)<\/item>/gi;
  const titleRegex = /<title[^>]*><!\[CDATA\[([\s\S]*?)\]\]><\/title>|<title[^>]*>([\s\S]*?)<\/title>/i;

  let itemMatch;
  while ((itemMatch = itemRegex.exec(xml)) !== null) {
    const itemXml = itemMatch[1];
    const titleMatch = titleRegex.exec(itemXml);
    if (titleMatch) {
      const title = cleanTitle(titleMatch[1] || titleMatch[2] || '');
      if (title.length > 20) {
        items.push(title);
      }
    }
  }
  return items;
}

// ─── REDDIT ───────────────────────────────────────────────────────────────────

async function fetchSubredditPosts(subreddit) {
  const url = `https://www.reddit.com/r/${subreddit}/hot.json?limit=5&t=day`;
  try {
    const response = await fetch(url, {
      headers: { 'User-Agent': 'MrOldverdict-Bot/1.0' }
    });
    if (!response.ok) return [];
    const data = await response.json();
    const posts = data?.data?.children || [];
    return posts
      .filter(post => !post.data.stickied && !post.data.over_18)
      .map(post => ({
        title: cleanTitle(post.data.title),
        score: post.data.score,
        comments: post.data.num_comments,
        subreddit: post.data.subreddit,
        source: `reddit/r/${post.data.subreddit}`
      }))
      .filter(post => post.title.length > 20);
  } catch {
    return [];
  }
}

function calculateEngagementScore(score, comments) {
  return score + (comments * 3);
}

// ─── GOOGLE TRENDS ────────────────────────────────────────────────────────────

async function fetchGoogleTrends(feedUrl, category) {
  try {
    const response = await fetch(feedUrl, {
      headers: { 'User-Agent': 'MrOldverdict-Bot/1.0' }
    });
    if (!response.ok) return [];
    const xml = await response.text();
    const titles = extractRSSItems(xml);
    return titles
      .filter(passesBlacklist)
      .slice(0, 5)
      .map(title => ({
        title,
        category,
        source: `google_trends/${feedUrl.includes('geo=US') ? 'US' : feedUrl.includes('geo=GB') ? 'GB' : 'AU'}`,
        engagementScore: 500  // Fixed mid-range score for trends
      }));
  } catch {
    return [];
  }
}

// ─── NEWS RSS ─────────────────────────────────────────────────────────────────

async function fetchNewsRSS(feedUrl, category) {
  try {
    const response = await fetch(feedUrl, {
      headers: { 'User-Agent': 'MrOldverdict-Bot/1.0' }
    });
    if (!response.ok) return [];
    const xml = await response.text();
    const titles = extractRSSItems(xml);

    // Filter out pure news headlines — keep behavior/trend focused ones
    // News titles with these words are too event-specific, not behavior topics
    const tooNewsyWords = ['killed', 'dies', 'arrest', 'court', 'trial', 'election', 'vote', 'minister', 'president', 'mp ', ' mp,'];
    const filtered = titles.filter(t => {
      const lower = t.toLowerCase();
      return passesBlacklist(t) && !tooNewsyWords.some(w => lower.includes(w));
    });

    return filtered.slice(0, 3).map(title => ({
      title,
      category,
      source: feedUrl.includes('bbc') ? 'bbc_news' : 'guardian_news',
      engagementScore: 400
    }));
  } catch {
    return [];
  }
}

// ─── HACKER NEWS ──────────────────────────────────────────────────────────────

async function fetchHackerNews() {
  try {
    // Get top story IDs
    const idsRes = await fetch('https://hacker-news.firebaseio.com/v0/topstories.json');
    if (!idsRes.ok) return [];
    const ids = await idsRes.json();
    const top10 = ids.slice(0, 10);

    // Fetch each story — limit to 6 to stay within subrequest budget
    const stories = await Promise.all(
      top10.slice(0, 6).map(async id => {
        try {
          const res = await fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
          if (!res.ok) return null;
          const item = await res.json();
          if (!item || item.type !== 'story' || !item.title) return null;
          return {
            title: cleanTitle(item.title),
            score: item.score || 0,
            comments: item.descendants || 0,
            source: 'hacker_news'
          };
        } catch {
          return null;
        }
      })
    );

    return stories
      .filter(s => s && s.title.length > 20 && passesBlacklist(s.title))
      .map(s => ({
        title: s.title,
        category: s.title.toLowerCase().includes('work') || s.title.toLowerCase().includes('job') || s.title.toLowerCase().includes('company') ? 'B' : 'E',
        source: 'hacker_news',
        engagementScore: calculateEngagementScore(s.score, s.comments)
      }));
  } catch {
    return [];
  }
}

// ─── SUPABASE ─────────────────────────────────────────────────────────────────

async function topicAlreadyExists(supabaseUrl, supabaseKey, title) {
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  try {
    const response = await fetch(
      `${supabaseUrl}/rest/v1/topics?raw_topic=ilike.*${encodeURIComponent(title.substring(0, 20))}*&created_at=gte.${sevenDaysAgo}&limit=1`,
      {
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`
        }
      }
    );
    if (!response.ok) return false;
    const existing = await response.json();
    return existing.length > 0;
  } catch {
    return false;
  }
}

async function storeTopic(supabaseUrl, supabaseKey, topic) {
  const response = await fetch(`${supabaseUrl}/rest/v1/topics`, {
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
  return response.ok;
}

// ─── MAIN INGESTION ───────────────────────────────────────────────────────────

async function runIngestion(env) {
  const results = {
    fetched: 0,
    passed_blacklist: 0,
    stored: 0,
    skipped_duplicate: 0,
    by_source: { reddit: 0, google_trends: 0, news_rss: 0, hacker_news: 0 },
    categories: { A: 0, B: 0, C: 0, D: 0, E: 0 }
  };

  const allTopics = [];

  // 1. Reddit
  for (const [category, subreddits] of Object.entries(SUBREDDITS)) {
    for (const subreddit of subreddits) {
      const posts = await fetchSubredditPosts(subreddit);
      results.fetched += posts.length;
      for (const post of posts) {
        if (!passesBlacklist(post.title)) continue;
        results.passed_blacklist++;
        allTopics.push({
          title: post.title,
          category,
          source: post.source,
          engagementScore: calculateEngagementScore(post.score, post.comments)
        });
      }
    }
  }

  // 2. Google Trends
  for (const feed of TRENDS_FEEDS) {
    const topics = await fetchGoogleTrends(feed.url, feed.category);
    results.fetched += topics.length;
    results.passed_blacklist += topics.length;
    allTopics.push(...topics);
  }

  // 3. News RSS
  for (const feed of NEWS_FEEDS) {
    const topics = await fetchNewsRSS(feed.url, feed.category);
    results.fetched += topics.length;
    results.passed_blacklist += topics.length;
    allTopics.push(...topics);
  }

  // 4. Hacker News
  const hnTopics = await fetchHackerNews();
  results.fetched += hnTopics.length;
  results.passed_blacklist += hnTopics.length;
  allTopics.push(...hnTopics);

  // Store top topics — deduplicate and store best per category
  const byCategory = { A: [], B: [], C: [], D: [], E: [] };
  for (const topic of allTopics) {
    if (byCategory[topic.category]) {
      byCategory[topic.category].push(topic);
    }
  }

  for (const [category, topics] of Object.entries(byCategory)) {
    const top5 = topics
      .sort((a, b) => b.engagementScore - a.engagementScore)
      .slice(0, 5);

    for (const topic of top5) {
      const isDuplicate = await topicAlreadyExists(env.SUPABASE_URL, env.SUPABASE_KEY, topic.title);
      if (isDuplicate) {
        results.skipped_duplicate++;
        continue;
      }
      const stored = await storeTopic(env.SUPABASE_URL, env.SUPABASE_KEY, topic);
      if (stored) {
        results.stored++;
        results.categories[category]++;
        // Track by source
        if (topic.source.startsWith('reddit')) results.by_source.reddit++;
        else if (topic.source.startsWith('google')) results.by_source.google_trends++;
        else if (topic.source.includes('news')) results.by_source.news_rss++;
        else if (topic.source === 'hacker_news') results.by_source.hacker_news++;
      }
    }
  }

  return results;
}

// ─── HANDLERS ─────────────────────────────────────────────────────────────────

export default {
  async fetch(request, env) {
    if (request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'Ingestion worker standing by.' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const authHeader = request.headers.get('Authorization');
    if (authHeader !== `Bearer ${env.COUNCIL_SECRET}`) {
      return new Response('Unauthorized', { status: 401 });
    }

    try {
      const results = await runIngestion(env);
      return new Response(JSON.stringify({
        success: true,
        message: 'Ingestion complete.',
        results
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      fetch(`https://${env.WORKER_DOMAIN}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.COUNCIL_SECRET}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
      })
    );
  }
};
