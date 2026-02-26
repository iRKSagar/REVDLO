// Mr. Oldverdict Ingestion Worker
// Pulls top posts from Reddit subreddits
// Scores them for virality, filters blacklist, assigns category, stores in Supabase

const SUBREDDITS = {
  A: ['mildlyinfuriating', 'firstworldproblems', 'technicallythetruth', 'humansbeingbros'],
  B: ['antiwork', 'jobs', 'careerguidance', 'WorkReform', 'LinkedInLunatics'],
  C: ['relationship_advice', 'AmItheAsshole', 'confession', 'lonely'],
  D: ['nosurf', 'digitalminimalism', 'Showerthoughts', 'Adulting'],
  E: ['Showerthoughts', 'Stoicism', 'history']
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
  // Remove special characters and clean up the title for use as a raw topic
  return title
    .replace(/[^\w\s.,?!'-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 280);
}

async function fetchSubredditPosts(subreddit) {
  // Use Reddit public JSON API - no key required
  const url = `https://www.reddit.com/r/${subreddit}/hot.json?limit=10&t=day`;
  
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'MrOldverdict-Bot/1.0'
      }
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
        url: `https://reddit.com${post.data.permalink}`
      }))
      .filter(post => post.title.length > 20);

  } catch (error) {
    console.error(`Failed to fetch r/${subreddit}:`, error.message);
    return [];
  }
}

function calculateEngagementScore(post) {
  // Weighted score: upvotes + (comments * 3)
  // Comments weighted higher because they indicate stronger reaction
  return post.score + (post.comments * 3);
}

async function topicAlreadyExists(supabaseUrl, supabaseKey, title) {
  // Check if a very similar topic was ingested in the last 7 days
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  
  const response = await fetch(
    `${supabaseUrl}/rest/v1/topics?raw_topic=ilike.*${encodeURIComponent(title.substring(0, 30))}*&created_at=gte.${sevenDaysAgo}&limit=1`,
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
        // Blacklist check
        if (!passesBlacklist(post.title)) continue;
        results.passed_blacklist++;

        // Calculate engagement score
        const engagementScore = calculateEngagementScore(post);

        categoryPosts.push({
          ...post,
          category,
          engagementScore
        });
      }
    }

    // Sort by engagement score, take top 5 per category
    const top5 = categoryPosts
      .sort((a, b) => b.engagementScore - a.engagementScore)
      .slice(0, 5);

    for (const post of top5) {
      // Duplicate check
      const isDuplicate = await topicAlreadyExists(env.SUPABASE_URL, env.SUPABASE_KEY, post.title);
      if (isDuplicate) {
        results.skipped_duplicate++;
        continue;
      }

      // Store in Supabase
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
    // Health check
    if (request.method === 'GET') {
      return new Response(JSON.stringify({ status: 'Ingestion worker standing by.' }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    // Auth check
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
      return new Response(JSON.stringify({
        error: error.message
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  },

  // Runs once daily at 6 AM UTC - feeds topics before the 11 AM publish window
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
