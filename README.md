# REVDLO - Council Engine

Been watching since before.

---

## What this is

The Council is the script generation engine for REVDLO. It receives a raw topic, checks its memory for related past scripts, generates a structured comedy script in Mr. Oldverdict's voice using GPT-4o, and stores everything in Supabase.

It runs automatically twice a day at 11 AM UTC and 8 PM UTC via a Cloudflare Worker cron trigger.

---

## Stack

- Cloudflare Workers for compute and scheduling
- Supabase for database and storage
- OpenAI GPT-4o for script generation

---

## Setup

### Step 1. Supabase

1. Go to your Supabase project
2. Open the SQL editor
3. Paste the contents of supabase/schema.sql and run it
4. Copy your project URL and anon key from Settings > API

### Step 2. Environment secrets

You need four secrets. Set each one using the Cloudflare dashboard or wrangler CLI.

```
wrangler secret put OPENAI_API_KEY
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_KEY
wrangler secret put COUNCIL_SECRET
```

COUNCIL_SECRET is a password you create yourself. Use any strong random string. It protects the worker endpoint from unauthorized calls.

### Step 3. Update wrangler.toml

Replace the WORKER_DOMAIN value with your actual Cloudflare Workers subdomain after first deploy.

### Step 4. Deploy

```
npm install -g wrangler
wrangler login
wrangler deploy
```

---

## How it works

### Automatic mode
The worker fires at 11 AM UTC and 8 PM UTC daily. It pulls the highest scoring unused topic from Supabase that has cleared the blacklist. If no topic is available it falls back to Category E automatically.

### Manual mode
POST to the worker endpoint with a topic and category.

```
POST https://your-worker-domain.workers.dev/
Authorization: Bearer YOUR_COUNCIL_SECRET
Content-Type: application/json

{
  "raw_topic": "People documenting every meal they eat online",
  "category": "A"
}
```

Categories are A, B, C, D, or E.

### Response

```json
{
  "success": true,
  "script_id": "uuid",
  "category": "A",
  "raw_topic": "People documenting every meal they eat online",
  "script": {
    "scene": "Mr. Oldverdict seated at a worn table. A young woman across from him photographs her food before touching it. He watches her.",
    "lines": [
      { "text": "The food is getting cold. But the memory is loading.", "pause_after": true }
    ],
    "prop": "none",
    "expression": "flat_observation",
    "theme_tags": ["food", "phones", "documentation", "modern_behavior"]
  },
  "memory_connections": 2
}
```

---

## Adding topics to the ingestion queue

Insert raw topics into the topics table in Supabase. Set blacklist_cleared to true only after verifying the topic passes the blacklist rules. Set engagement_score based on the virality scoring system.

```sql
INSERT INTO topics (raw_topic, category, source, engagement_score, blacklist_cleared)
VALUES ('People hiring coaches to teach them how to rest', 'A', 'reddit', 8500, true);
```

---

## Files

```
REVDLO/
  council-worker/
    src/
      index.js        The Council engine
    wrangler.toml     Cloudflare deployment config
  supabase/
    schema.sql        Database schema
  README.md           This file
```

---

## What comes next

- Ingestion worker: pulls from Reddit, Twitter, YouTube, Google Trends daily
- Image generation worker: takes scene direction and generates REVDLO image
- Voice generation worker: sends script lines to ElevenLabs and returns audio file
- Assembly worker: combines image, voice, and captions into a vertical video
- Publishing worker: pushes to YouTube Shorts and Instagram Reels on schedule
