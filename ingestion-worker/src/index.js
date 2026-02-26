// Mr. Oldverdict Ingestion Worker
// Pulls top posts from Reddit subreddits
// Reduced to 2 subreddits per category to stay within Cloudflare free tier subrequest limits

const SUBREDDITS = {
  A: ['mildlyinfuriating', 'firstworldproblems'],
  B: ['antiwork', 'LinkedInLunatics'],
  C: ['AmItheAsshole', 'confession'],
  D: ['nosurf', 'Showerthoughts'],
  E: ['Stoicism', 'history']
};

const BLACKLIST_KEYWORDS = [
  'trump', 'biden', 'obama', 'modi', 'putin', 'xi', 'sunak', 'labour', 'republican', 'democrat',
  'conservative', 'liberal', 'maga', 'woke', 'israel', 'palestine', 'ukraine', 'russia', 'china',
  'christian', 'muslim', 'islam', 'hindu', 'jewish', 'bible', 'quran', 'torah',
  'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'instagram', 'tiktok', 'twitter', 'netflix',
  'elon', 'musk', 'bezos', 'zuckerberg', 'epstein', 'kardashian',
  'rape', 'suicide', 'murder', 'abuse', 'racist', 'nazi', 'genocide', 'terrorist',
  'porn', 'sex', 'nsfw', 'nude', 'naked'
];

function passesBlacklist(text) {
  const lower = text.toLowerCase();
  return !BLACKLIST_KEYWORDS.some(word => lower.includes(word));
}

function cleanTitle(title) {
  return title
    .replace(/[^\w\s.,?!'-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 280);
}

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
        subreddit: post.data.subreddit
      }))
      .filter(post => post.title.length > 20);
  } catch (error) {
    return [];
  }
}

function calculateEngagementScore(post) {
  return post.score + (post.comments * 3);
}

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
      source: `reddit/r/${topic.subreddit}`,
      engagement_score: topic.engagementScore,
      blacklist_cleared: true
    })
  });
  return response.ok;
}

async function runIngestion(env) {
  const results = {
    fetched: 0,
    passed_blacklist: 0,
    stored: 0,
    skipped_duplicate: 0,
    categories: { A: 0, B: 0, C: 0, D: 0, E: 0 }
  };

  for (const [category, subreddits] of Object.entries(SUBREDDITS)) {
    const categoryPosts = [];

    for (const subreddit of subreddits) {
      const posts = await fetchSubredditPosts(subreddit);
      results.fetched += posts.length;

      for (const post of posts) {
        if (!passesBlacklist(post.title)) continue;
        results.passed_blacklist++;
        categoryPosts.push({
          ...post,
          category,
          engagementScore: calculateEngagementScore(post)
        });
      }
    }

    const top3 = categoryPosts
      .sort((a, b) => b.engagementScore - a.engagementScore)
      .slice(0, 3);

    for (const post of top3) {
      const isDuplicate = await topicAlreadyExists(env.SUPABASE_URL, env.SUPABASE_KEY, post.title);
      if (isDuplicate) {
        results.skipped_duplicate++;
        continue;
      }
      const stored = await storeTopic(env.SUPABASE_URL, env.SUPABASE_KEY, post);
      if (stored) {
        results.stored++;
        results.categories[category]++;
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
