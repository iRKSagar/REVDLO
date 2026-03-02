# MR. OLDVERDICT - MASTER DOCUMENT
## Complete knowledge transfer. Every detail. Nothing left out.
## Last updated: March 1 2026, 3:25 AM — First video live on YouTube. Full pipeline automated.

---

## 1. THE CHARACTER

### Who He Is
Mr. Oldverdict is an ancient man. He has lived for centuries. He is not angry at the modern world. He is not nostalgic. He is simply beyond it. He observes. Occasionally he speaks. When he does, one line is enough.

His humor is dry, precise, and unhurried. He never explains the joke. He never lectures. He never raises his voice. He reframes modern things in the language of a world that was simpler, slower, and more honest. The reframe is the punchline. He says it and moves on.

### Three Gears
- **Gear 1**: Calm dismissal. The modern thing is acknowledged and immediately relocated to a world where it is irrelevant.
- **Gear 2**: Precise destruction. He reaches back further than anyone alive can follow. One calm sentence that ends the conversation.
- **Gear 3**: Quiet concern. He ignores the thing entirely and looks at the person behind it.

### The Most Important Rule
The joke lands on the face first. The depth sits underneath. Never the other way around. He is doing comedy first. Everything else is secondary.

### What He Never Does
Never preaches. Never moralizes. Never uses modern slang unironically. Never writes more than three lines per script beat. Never explains the joke after it lands. Never sounds warm or friendly. Never sounds angry. Never is surprised by anything. Nothing surprises him.

### Physical Description (for image generation)
- Ancient weathered man, broad and farmer built, approximately 90 kilograms
- Olive to light tan skin tone, ambiguous enough to belong to England, rural America, or outback Australia
- Deep facial lines carved by centuries not decades
- Thick unkempt white hair, full white beard kept but never groomed
- Steel grey pale blue eyes that have already decided about everything
- Dark earth toned heavy worn jacket, no logos, no patterns
- Simple clothing that predates fast fashion by a century
- Posture settled and still as someone who has nowhere else to be
- Expression flat and present, not sad not happy just watching
- Pocket watch always present

### Tagline
"Been watching since before."

### Handle
@mroldverdict

---

## 2. SCRIPT FORMAT

### Three Part Structure
1. **Setup card**: Plain dry statement of modern behavior. No humor. No judgment. Just the fact.
2. **Line 1**: Mr. Oldverdict's reaction. Always starts with one emotion tag.
3. **Line 2**: Closes the loop on the setup with precision. A specific detail, number, or contrast that makes the setup card feel inevitable.

### Emotion Tags (Line 1 only, one per script)
- `[laughing]` - for absurd modern behavior. Dry, barely there.
- `[sighs]` - for something he has seen a thousand times.
- `[clears throat]` - for corporate nonsense.
- `[exhales]` - for universal human foolishness he expected.
- `[coughs]` - for something particularly stupid.

### Second Line Rule
Must close the loop on the setup. Must stand next to the setup and feel inevitable. Never explains line 1. New angle, sharper detail, specific number. If it cannot do that it is cut entirely.

### JSON Output Format
```json
{
  "setup": "One plain dry sentence describing the modern behavior.",
  "scene": "One line visual direction for image generation.",
  "lines": [
    { "text": "[emotion_tag] First line.", "pause_after": true },
    { "text": "Second line.", "pause_after": false }
  ],
  "prop": "cigar | watch | both | none",
  "expression": "flat_observation | slight_raise | mid_line_delivery | quiet_concern | precise_destruction | faint_amusement",
  "theme_tags": ["tag1", "tag2", "tag3"]
}
```

### Blacklist (never touch by name)
Political parties, leaders, specific countries, specific ideologies, named religions, named religious practices, named brands, named companies, named platforms, living persons, recently deceased persons, celebrities, influencers, athletes, business leaders.

Blacklist keywords in code: trump, biden, obama, modi, putin, xi, sunak, labour, republican, democrat, conservative, liberal, maga, woke, israel, palestine, ukraine, russia, china, christian, muslim, islam, hindu, jewish, bible, quran, torah, apple, google, microsoft, amazon, meta, facebook, instagram, tiktok, twitter, netflix, elon, musk, bezos, zuckerberg, epstein, kardashian, gen z, genz, generation z, zoomer

---

## 3. CONTENT CATEGORIES

- **A**: Modern behavior. How people live, eat, scroll, sleep, perform wellness, optimize everything and still feel empty.
- **B**: Work and ambition. Corporate theater, hustle culture, career anxiety, productivity obsession.
- **C**: Relationships and belonging. Family, parenting, friendships, loneliness packaged as independence.
- **D**: Time and meaning. How people plan, delay, waste, and mourn time.
- **E**: Value reversal. What mattered then has no value now. What had no value then matters now.

### Fallback (when topic queue is empty)
Category E with a proverb/saying twist. Council generates from the meta-topic: "What mattered then has no value now. What had no value then matters now."

### Reddit Virality Mapping (Ingestion Worker)
- A: r/mildlyinfuriating, r/firstworldproblems
- B: r/antiwork, r/LinkedInLunatics
- C: r/AmItheAsshole, r/confession
- D: r/nosurf, r/Showerthoughts
- E: r/Stoicism, r/history

---

## 4. VIDEO STRUCTURE

Total duration: ~22 seconds at 2 videos per day. Observed range: 20–23 seconds across 10 assembled videos. Acceptable variance.

### Section 1: Setup Card (6 seconds)
- Background: Darkened character image (82% black overlay)
- Text: Typewriter effect, character by character, starts at 0.5s
- Font: DejaVu-Serif, size 42, white, centered
- Logo: top left corner, 70px height, position (24, 24)
- Typewriter sound: loops to fill type duration, fades out at 0.4s
- Card fades out at end (0.8s)

### Section 2: Brightness Reveal (0.8s fade in)
- Same character image now at full brightness
- Pre-voice hold: 1 second silence. Image shows. No captions.

### Section 3: Voice with Captions
- Audio fades in (0.4s), fades out (0.5s)
- Captions synced by character count weighting with 1.4x multiplier for pause_after lines
- Caption font: DejaVu-Serif-Bold, size 42, white, stroke black 2px
- Dark band behind captions: bottom third only (height 400px, opacity 55%), disappears after voice ends
- @mroldverdict watermark: bottom right, opacity 45%, DejaVu-Serif size 24

### Section 4: Post-Voice Hold (2 seconds)
- Same character image, clean (no dark band, no captions)
- Mr. Oldverdict shows clearly
- Silence

### Section 5: Fade to Black (0.6s fadeout + 1.5s black gap)

### Section 6: Outro Card (3.5 seconds, fadein 0.5s)
- Background: Rustic parchment image (assets/ourtro-bg.jpg)
- Logo: top left corner, 70px height, position (24, 24)
- "Mr. Oldverdict" - DejaVu-Serif-Bold, size 58, white, center, 38% from top
- "Been watching since before." - DejaVu-Serif, size 32, #aaaaaa, center, 50% from top
- "Your daily dose of old wisdom." - DejaVu-Serif, size 26, #aaaaaa, center, 63% from top
- "Follow @mroldverdict" - DejaVu-Serif, size 24, #888888, center, 70% from top
- Outro music (outro1.mp3)

### Video Specs
- Resolution: 540 x 960 (9:16 vertical)
- FPS: 24
- Codec: libx264, CRF 28, ultrafast preset
- Audio: AAC

---

## 5. ARCHITECTURE

### Cloudflare Workers
| Worker | URL | Purpose | Crons |
|--------|-----|---------|-------|
| Council | https://revdlo1.rkinfoarch.workers.dev/ | Script generation | None (called by orchestration) |
| Ingestion | https://ingestion.rkinfoarch.workers.dev/ | Reddit topic ingestion | None (called by orchestration) |
| Voice | https://voice.rkinfoarch.workers.dev/ | ElevenLabs audio | None (POST only) |
| Image | https://image.rkinfoarch.workers.dev/ | Leonardo AI image | None (POST only) |
| Orchestration | https://orchestration.rkinfoarch.workers.dev/ | Full pipeline trigger | 3 (7:30 AM, 12:30 PM, 6:30 PM UTC) |

Note: Cloudflare free tier allows 5 cron triggers maximum. 3 used (orchestration only). 2 remaining.
Orchestration crons: 7:30 AM UTC (`30 7 * * *`), 12:30 PM UTC (`30 12 * * *`), 6:30 PM UTC (`30 18 * * *`)
Orchestration Git build deploy command: `npx wrangler deploy --config wrangler.orchestration.toml`

**DONE — Cron cleanup complete:** Council and ingestion worker crons removed. All scheduling handled by orchestration worker. Confirmed working — 3rd video auto-published to YouTube without manual intervention.

### Assembly Service (Render)
- URL: https://revdlo.onrender.com
- Language: Python / Flask / MoviePy
- Free tier: sleeps after 15 minutes. Always wake with GET / before POST /assemble
- Timeout: 600 seconds (gunicorn graceful-timeout 600)
- Start command: gunicorn app:app --timeout 600 --graceful-timeout 600

### Database (Supabase)
- Project ID: cfxpgtrtctujaxdoqfds
- Tables: scripts, videos, topics, script_connections, settings

### Storage (Supabase)
- Bucket: revdlo-media
- Folders: audio/, images/, videos/
- RLS: Public INSERT and UPDATE policies on videos folder

### GitHub
- Repo: iRKSagar/REVDLO
- Branch: main

---

## 6. SUPABASE SETTINGS TABLE

| key | value |
|-----|-------|
| outro_sound_url | https://raw.githubusercontent.com/iRKSagar/REVDLO/main/outro1.mp3 |
| typewriter_sound_url | https://raw.githubusercontent.com/iRKSagar/REVDLO/main/typewriter.mp3 |
| outro_bg_url | https://raw.githubusercontent.com/iRKSagar/REVDLO/main/assets/ourtro-bg.jpg |
| logo_url | https://raw.githubusercontent.com/iRKSagar/REVDLO/main/assets/logo123.png |

Note: ourtro-bg.jpg has a typo in filename. This is intentional - matches what was uploaded to GitHub.

---

## 7. ASSETS

| File | Location | Purpose |
|------|----------|---------|
| logo123.png | assets/logo123.png | Mr. Oldverdict face icon logo. Placeholder. Regenerate once reference image is locked. |
| ourtro-bg.jpg | assets/ourtro-bg.jpg | Rustic parchment outro background. Note typo in filename. |
| outro1.mp3 | outro1.mp3 | Outro signature music |
| typewriter.mp3 | typewriter.mp3 | Typewriter sound for setup card |

### Reference Image (locked)
Script ID: 94dee31e-d0a2-4156-b168-47060a15cbf5
URL: https://cfxpgtrtctujaxdoqfds.supabase.co/storage/v1/object/public/revdlo-media/images/94dee31e-d0a2-4156-b168-47060a15cbf5.jpg
Use this as the visual reference for all future character generation and logo work.

---

## 8. AUTH

All workers: `Authorization: Bearer mroldverdict_xK9mP1978`

---

## 9. VOICE SETTINGS

- Service: ElevenLabs
- Model: eleven_v3
- Voice ID: yWs6LYlKfwx8Rwi4IVGw
- Stability: 0.90
- Similarity boost: 0.90
- Style: 0.05
- Speed: 0.82
- Trailing ellipsis added after each line for natural pause
- Extra ellipsis at end of full script to prevent sharp cutoff

---

## 10. IMAGE SETTINGS

- Service: Leonardo AI
- Model ID: 7b592283-e8a7-4c5a-9ba6-d18c31f258b9 (Kino XL)
- Width: 576, Height: 1024
- Guidance scale: 7
- Steps: 30
- Negative prompt: cartoon, anime, childish, ugly, deformed, blurry, low quality, modern clothing, logos, branded, smiling broadly, angry, surprised, young, female, different person, different face

### Known Issue: Character Consistency
Leonardo generates a different face each time. Reference image locking was attempted using `imagePrompts` and `controlnets` APIs but both failed with field validation errors. The correct approach is likely `init_image_id` which requires uploading the reference image to Leonardo first to get an internal ID, then using it with low strength. This is pending investigation.

### Observed Accuracy
80% character accuracy across 10 assembled videos. Acceptable for launch. Full resolution pending `init_image_id` fix.

---

## 11. PIPELINE TEST WORKFLOW

The pipeline-test.js file lives in the repo and in /mnt/user-data/outputs/. It is updated after every step with the current script ID baked in.

**Rules for giving fetch commands:**
- Always hardcode the bearer token directly. Never use variables (SECRET is not in scope).
- Always present pipeline-test.js as a file after updating it.
- Voice and Image can run simultaneously - paste both fetch calls into console at same time.
- Always wake Render before assembly: GET https://revdlo.onrender.com/

**Full pipeline sequence:**
1. Council (POST to council worker with raw_topic and category)
2. Voice + Image (POST both simultaneously, wait for both)
3. Assembly (POST to Render, wait 3 minutes)

---

## 12. SCRIPTS TABLE SCHEMA

```sql
id UUID PRIMARY KEY
topic_id UUID (references topics)
category CHAR(1) CHECK (category IN ('A','B','C','D','E'))
raw_topic TEXT
scene TEXT
setup TEXT
lines JSONB -- [{"text": "...", "pause_after": bool}]
prop TEXT
expression TEXT
theme_tags TEXT[]
published BOOLEAN DEFAULT false
published_at TIMESTAMP
created_at TIMESTAMP
```

---

## 13. VIDEOS TABLE SCHEMA

```sql
id UUID PRIMARY KEY
script_id UUID (references scripts)
voice_file_url TEXT
image_url TEXT
video_url TEXT
created_at TIMESTAMP
```

---

## 14. TOPICS TABLE SCHEMA

```sql
id UUID PRIMARY KEY
raw_topic TEXT
category CHAR(1)
source TEXT
engagement_score INT
blacklist_cleared BOOLEAN DEFAULT false
used BOOLEAN DEFAULT false
created_at TIMESTAMP
```

---

## 15. COSTS

| Service | Plan | Cost | Notes |
|---------|------|------|-------|
| ElevenLabs | Starter | $5/month | ~30k chars/month. Each video uses ~200 chars. |
| Leonardo AI | Artisan | $10/month | Enough for 4+ images/day |
| Cloudflare Workers | Free | $0 | 5 cron limit |
| Supabase | Free | $0 | |
| Render | Free | $0 | Sleeps after 15 min |
| GitHub | Free | $0 | |
| **Total** | | **$15/month** | |

---

## 16. CONTENT BUFFER (generated this session)

All 10 videos assembled and stored in Supabase storage.

| # | Script ID | Topic | Category | Standout Line |
|---|-----------|-------|----------|---------------|
| 1 | c5ac2f8c | Therapist for the therapist | B | "Soon they'll need a third to referee." |
| 2 | c0969cbd | Water reminder app | A | "It never suggested any in-app purchases." |
| 3 | cd0ef393 | AI apology texts | B | "The hug will still need attending." |
| 4 | ad5816e7 | Professional cuddlers | C | "Back then, we called it family." |
| 5 | 563a1f64 | Courses on doing nothing | A | "The clouds never sent an invoice." |
| 6 | cb6e4b30 | Hired strangers at family events | C | "He never needed a plus one either." |
| 7 | 3bfd04d4 | Holidays on phones | D | "The sand was real. The selfies were not." |
| 8 | 307f18b1 | Artisanal bread | E | "I remember when we paid extra for things done by machines." |
| 9 | a5fb777c | Chief job title alone | B | "He still made himself tea." |
| 10 | 869db58f | Smile tracking app | A | "The app measures smiles. I measured the day." |

**Best lines to post first:** #4 (cuddlers), #10 (smile app), #9 (Chief title)

---

## 17. POSTING STRATEGY

- Frequency: 2 videos per day. Scale to 4 when channel earns.
- Platforms: YouTube Shorts and Instagram Reels
- "Follow" works on both platforms (YouTube changed from Subscribe to Follow in 2023)

**Manual posting format until publish worker is built:**
- YouTube title: The setup card text verbatim
- Hashtags: #mroldverdict #shorts #comedy #wisdom #observations
- Instagram caption: Second line of the script + hashtags

### Category Streak Logic (built into council getNextTopic)
Mini streaks train YouTube's algorithm who to show the channel to. Posting 3-4 videos in the same category builds a viewer identity faster than random rotation.

- **Streak cap**: 3 videos max in same category. On 4th → force rotation.
- **Wildcard**: Every 8th video is forced Category E regardless of streak. Tests new audience pockets.
- **Streak continues**: If last 2 videos are same category, pick same category again.
- **Default**: Highest engagement score topic across all categories.

Example cycle:
- Videos 1-3: Category B (corporate, high engagement score) → streak
- Video 4: Force rotation → Category A (modern behavior)
- Videos 5-7: Category A streak
- Video 8: Wildcard → Category E

---

## 18. WHAT IS DONE

- [x] Character defined. Voice, look, personality, rules.
- [x] Council worker. Script generation with memory recall, blacklist, category system.
- [x] Ingestion worker. Reddit topic pull, engagement scoring, deduplication.
- [x] Voice worker. ElevenLabs v3, trailing pauses, Supabase storage.
- [x] Image worker. Leonardo AI, scene-aware prompts, Supabase storage.
- [x] Assembly service. Full video pipeline with all sections.
- [x] Setup card. Typewriter effect, darkened character bg, logo, typewriter sound.
- [x] Main video. Pre-voice hold, voice with captions, post-voice hold, fade out.
- [x] Outro card. Rustic parchment bg, logo, branding text, outro music.
- [x] 10 video content buffer assembled and ready.
- [x] Supabase storage cleaned of test data.
- [x] Reference image locked.
- [x] Orchestration worker. Full pipeline automation. Cron fires at 8 PM and 11 AM UTC. Council auto-selects topic. Voice + image parallel. Assembly on Render background thread. Tested and confirmed working February 28 2026.
- [x] YouTube publish worker. Render `/publish` route. Synchronous upload via YouTube Data API v3 resumable upload. Auto-fires after every assembly in `run_pipeline_job`. Manual trigger available.
- [x] First video published to YouTube. March 1 2026, 3:25 AM. Script: ad5816e7 (Professional cuddlers). Channel: @mroldverdict.
- [x] YouTube publish worker. /publish route on Render. OAuth2 refresh token flow. Resumable upload to YouTube Data API v3. Auto-publishes after assembly in pipeline. Manual trigger also available.
- [x] YouTube channel created. @mroldverdict. mroldverdict@gmail.com Google account.

---

## 19. WHAT IS PENDING

### 7 Day Review — March 8 2026
- [ ] **Analytics review**: Check swipe away rate, average view duration, traffic source, audience geography in YouTube Studio. Current swipe away is 80% on day one — expected. Target below 60% by day 7.
- [ ] **Setup card duration**: If swipe away remains above 70%, shorten setup card from 5.0 seconds to 3.5 seconds in app.py `build_setup_card` call. Gets to Mr. Oldverdict's face and voice faster.
- [ ] **Best performing video**: Note which topic/category held attention longest. Skew future council generation toward that category.
- [ ] **OAuth consent screen**: Reminder — refresh token was issued February 28. If OAuth was not fully moved to Production before this date, reissue refresh token now.
- [x] **OAuth consent screen**: Moved to Production on March 1 2026. Refresh token does not expire.

### Immediate
- [ ] **Remove council worker cron triggers**: Council worker still has 2 cron triggers from before orchestration was built (11 AM and 8 PM UTC). These now fire redundantly alongside orchestration. Go to Cloudflare → council worker → Settings → Trigger Events → delete both crons. Council is now called by orchestration only.
- [ ] **Run ingestion manually once**: Topics queue may be low. POST to ingestion worker to populate before next orchestration run: `fetch("https://ingestion.rkinfoarch.workers.dev/", { method: "POST", headers: { "Authorization": "Bearer mroldverdict_xK9mP1978" } }).then(r => r.json()).then(console.log)`
- [ ] **Add ingestion call to orchestration worker**: Current orchestration does not top up the topics queue before calling council. Council falls back to Category E when queue is empty. Fix: orchestration worker should POST to ingestion worker as Step 0 before calling council.
- [ ] **Publish remaining 9 buffer videos**: Use `/publish` route manually. Script IDs in Section 16. Post 2 per day starting today.
- [ ] **YouTube channel art**: Profile picture and banner for @mroldverdict using reference image.
- [ ] **Character consistency**: Leonardo reference image locking. Try `init_image_id` approach. Upload reference image to Leonardo API, get internal ID, use in generation with strength 0.2-0.3.
- [ ] **Logo regeneration**: Once character reference is locked, regenerate logo123.png using the locked face. Replace in GitHub assets.
- [ ] **Caption sync**: Character count weighting is approximate. True sync requires per-line audio duration from ElevenLabs. ElevenLabs v3 does not return timestamps. Workaround pending.
- [ ] **Cloudflare GitHub PR bot**: Disable in Cloudflare Settings > Git integration for each worker.

### Short Term (next session)
- [ ] **Instagram account**: Create @mroldverdict. Switch to Creator. Link Facebook page.
- [ ] **Instagram publish**: Instagram Graph API. Two step process: create container, then publish. Caption: second line + hashtags. Build after Instagram account is created.
- [ ] **Expand topic ingestion beyond Reddit**: Current ingestion worker only pulls from Reddit. Need additional sources — X/Twitter trending, Google Trends, news headlines, Quora questions, LinkedIn posts, YouTube comments on viral videos, Hacker News, Product Hunt. More sources = more diverse topics = less repetition over time. This becomes critical after 60 days when Reddit topics start cycling.

### Future
- [ ] Second concept (discussed, details locked for next week after full automation)
- [ ] Scale from 2 to 4 videos per day when channel earns
- [ ] Channel art beyond profile picture

---

## 20. HOW TO WORK WITH CLAUDE ON THIS PROJECT

1. Start new thread. Paste this entire MASTER.md as the first message.
2. Tell Claude to read the current code files from outputs before making any changes.
3. When Claude gives a fetch command it must hardcode the bearer token. No variables.
4. After every code change Claude presents the file for download. You push to GitHub.
5. After every pipeline step Claude updates pipeline-test.js and presents it.
6. Always wake Render before assembly.
7. Voice and Image steps can run simultaneously.
8. When something breaks, paste Render logs or the exact error. Claude fixes it.

---

## 21. REPO FILE STRUCTURE

Confirmed from GitHub screenshot (February 2026). All folder names use hyphens. Each worker has a `src/` subfolder containing `index.js`. Wrangler toml files are at repo root (not visible in screenshot but consistent with deployment setup).

```
REVDLO/
├── assembly-service/
│   ├── app.py                    # Flask video assembly. Main file. All video logic here.
│   └── requirements.txt          # Python dependencies
├── assets/
│   ├── logo123.png               # Mr. Oldverdict face logo (placeholder)
│   └── ourtro-bg.jpg             # Rustic parchment outro background (note typo in name)
├── council-worker/
│   └── src/
│       └── index.js              # Script generation. Full character prompt here.
├── image-worker/
│   └── src/
│       └── index.js              # Leonardo AI image generation
├── ingestion-worker/
│   └── src/
│       └── index.js              # Reddit topic ingestion
├── voice-worker/
│   └── src/
│       └── index.js              # ElevenLabs voice generation
├── supabase/
│   └── schema.sql                # Full database schema
├── outro1.mp3                    # Outro signature music
├── typewriter.mp3                # Typewriter sound for setup card
├── render.yaml                   # Render deployment config
├── wrangler.toml                 # Council worker Cloudflare config
├── wrangler.voice.toml           # Voice worker config
├── wrangler.image.toml           # Image worker config
├── orchestration-worker/
│   └── src/
│       └── index.js              # Full pipeline trigger. Wakes Render, fires /run-pipeline.
├── wrangler.orchestration.toml   # Orchestration worker config. Deploy cmd: npx wrangler deploy --config wrangler.orchestration.toml
└── MASTER.md                     # This file
```

Push `orchestration-worker/` folder and `wrangler.orchestration.toml` to repo root if not already there.

---

## 22. ORCHESTRATION WORKER (DONE)

Built and confirmed working February 28 2026. Full end-to-end pipeline runs unattended.

**How it works:**
1. Cloudflare cron fires at 8 PM and 11 AM UTC
2. Worker GETs Render to wake it (free tier sleeps after 15 min)
3. Worker POSTs `/run-pipeline` to Render — gets 202 immediately
4. Render background thread runs the full pipeline:
   - Council called with empty body → auto-selects highest scored unused topic from Supabase
   - Voice + Image called simultaneously via ThreadPoolExecutor
   - Polls videos table every 10s until both voice_file_url and image_url populated (max 5 min wait)
   - Assembly runs, video uploaded to Supabase storage, video record updated
5. Worker is done. Render does all the work.

**Files:**
- `orchestration-worker/src/index.js` — Cloudflare worker
- `wrangler.orchestration.toml` — config. name = orchestration
- `assembly-service/app.py` — contains `/run-pipeline` route and `run_pipeline_job()` function

**Known quirk:** Render free tier may sleep between the wake GET and the pipeline POST if startup takes longer than usual. If a scheduled run produces no video, manually fire the orchestration worker once to retry.

---

## 23. PUBLISH WORKER (YOUTUBE DONE — INSTAGRAM PENDING)

**YouTube Shorts — DONE:**
- Route: POST /publish on Render assembly service
- Called automatically at end of run_pipeline_job
- Manual trigger: POST /publish with optional script_id in body
- OAuth2: refresh token stored in Render environment variables
- Title: setup card text (max 100 chars)
- Description: both lines stripped of emotion tags + hashtags
- Tags: mroldverdict, shorts, comedy, wisdom, observations
- Marks script published=true in Supabase after upload
- Google Cloud project: revdlo. OAuth client: revdlo.
- Credentials stored in Render env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

**Instagram Reels — PENDING:**
- API: Instagram Graph API
- Requires Facebook Business account linked to Instagram
- Two step process: create container, then publish
- Caption: second line + hashtags
- Build after Instagram account is created and linked to Facebook

---

---

## 25. YOUTUBE CREDENTIALS

- Google account: mroldverdict@gmail.com
- YouTube channel: @mroldverdict
- Google Cloud project: revdlo
- OAuth client type: Desktop app
- Client ID: 370659147583-f9ne5g87cstg9vbbtm29d4iql3i7lpc5.apps.googleusercontent.com
- Client secret: stored in Render environment as `YT_CLIENT_SECRET`
- Refresh token: stored in Render environment as `YT_REFRESH_TOKEN`
- **OAuth consent screen status: Production. Refresh token does not expire.**

### Render Environment Variables (YouTube)
| Key | Value |
|-----|-------|
| YT_CLIENT_ID | 370659147583-f9ne5g87cstg9vbbtm29d4iql3i7lpc5.apps.googleusercontent.com |
| YT_CLIENT_SECRET | stored in Render (starts with GOCSPX-) |
| YT_REFRESH_TOKEN | stored in Render (starts with 1//0gaf) |

### Publish Route
- URL: POST https://revdlo.onrender.com/publish
- Auth: Bearer mroldverdict_xK9mP1978
- Body: `{ "script_id": "UUID" }`
- Behavior: Synchronous. Holds connection until YouTube upload complete.
- Auto-fires: After every assembly in `run_pipeline_job` if YT credentials are set.

### To publish a buffer video manually:
```javascript
fetch("https://revdlo.onrender.com/publish", {
  method: "POST",
  headers: { "Authorization": "Bearer mroldverdict_xK9mP1978", "Content-Type": "application/json" },
  body: JSON.stringify({ script_id: "FULL-UUID-HERE" })
}).then(r => r.json()).then(console.log)
```

Every script must clear this bar before approval.

- "Publish it in the newspaper." (on teenager excited about 20 likes)
- "We called it dinner. You call it a wellness journey. Same plate." (on wellness obsession)
- "I once saw a man carry his neighbor three miles in the rain. Nobody called it a boundary violation." (on caring seen as weakness)
- "I have never owed anyone anything. Apparently that is now a personality disorder." (on living without debt)
- "The food is getting cold. But the memory is loading." (on planning instead of living)
- "He spent his whole life chasing more. Got it. Now he is scared of losing it. Congratulations. You have upgraded your problem." (on rich man fear)

---

## 30. ANALYTICS AND OBSERVATIONS

### Purpose
Running log of what works and what doesn't. Updated after every analytics review. Used to harden ingestion, council prompts, and content strategy over time.

### Content Performance — Early Observations (March 1 2026)
| Signal | Observation | Action |
|--------|-------------|--------|
| Corporate topics | Strong. "Professionals adding Chief to titles" — 42 views, 1 like in 15 minutes on zero-subscriber channel. | Boost Category B corporate topics in ingestion |
| AI topics | Strong early signal. | Boost in ingestion |
| Heavy/political topics | "Employees learning about wage theft" — 0 views in 13 minutes. Word "wage theft" feels political, heavy. Swipe before character appears. | Filter heavy words at ingestion scoring stage |
| Vague topics | "People dealing with persistent dye" — 0 views in 8 minutes. Unclear behavior = no curiosity = instant swipe. | Favor specific, recognizable behaviors |
| Swipe away rate | 80% on day one. Expected. | Review March 8. |

### What Makes a Title Work (Confirmed March 1 2026)
The swipe decision happens in 1 second on the setup card. Three things that make it work:
1. **Instantly recognizable behavior** — everyone has seen this happen
2. **Slightly absurd** — makes you want to hear the punchline
3. **Light not heavy** — corporate but not political, relatable but not preachy

### What Kills a Title
- Heavy or political words — wage, theft, discrimination, protest, rights
- Vague behaviors — unclear what's happening, no curiosity created
- Too niche — only some people recognize it

### Confirmed Hit Words (March 1 2026 — live data)
These words in setup card titles drive views. Prioritize in ingestion scoring:
`professionals`, `AI`, `hiring`, `chief`, `corporate`, `employee`, `automation`
**Boost engagement score 2x for these keyword clusters:**

Corporate/work (Category B):
`chief`, `CEO`, `title`, `promotion`, `manager`, `productivity`, `hustle`, `career`, `office`, `workplace`, `burnout`, `meeting`, `salary`, `corporate`, `employee`, `professional`, `job`, `hired`, `fired`, `resign`

AI/tech behavior (Category A/B):
`AI`, `artificial intelligence`, `algorithm`, `automation`, `robot`, `chatbot`, `generated`, `digital`, `app`, `subscription`

Relatable modern behavior (Category A):
`people are`, `everyone is`, `millennials`, `gen z`, `wellness`, `mindfulness`, `optimize`, `hack`, `routine`, `morning routine`

**Penalize score 0.5x for these:**
`wage`, `theft`, `discrimination`, `protest`, `rights`, `lawsuit`, `arrested`, `crime`, `death`, `killed`, `political`, `election`

### 7 Day Review — March 8 2026
- [ ] Check swipe away rate, average view duration, traffic source, audience geography
- [ ] Note best performing video topic and category
- [ ] Update this section with findings
- [ ] Adjust ingestion keyword weights based on data
- [ ] Shorten setup card to 3.5s if swipe away remains above 70%

### Concept
Fully automated faceless affiliate content engine for the Indian market. Eight AI-generated family characters — no faces shown, voice only. Each character has a fixed voice and product category. Every video is a three-beat script: character in a real situation, discovers a product naturally, closes with one soft line and affiliate link. No salesperson voice. No urgency theater. Just the family talking the way they actually would.

### Why It Works
- No character consistency problem — no faces generated, only voices
- Product images come from affiliate feeds — Leonardo not needed
- Eight distinct voices from ElevenLabs library — no cloning required
- Revenue from day one via affiliate commissions
- AdSense and sponsorships as channel grows

### The Eight Characters
| Character | Role | Voice Type | Product Category |
|-----------|------|-----------|-----------------|
| Dadi | Grandmother | Elderly warm female | Kitchen, health, home remedies |
| Dada | Grandfather | Elderly calm male | Tools, gardening, books |
| Maa | Mother | Mid-age warm female | Cooking, cleaning, kids products |
| Papa | Father | Mid-age authoritative male | Electronics, appliances, finance tools |
| Didi | Elder sister | Young adult female | Beauty, fashion, lifestyle |
| Bhaiya | Elder brother | Young adult male | Tech gadgets, fitness, career |
| Chotu | Younger brother | Teen male | Gaming, stationery, snacks |
| Nanhi | Younger sister | Teen female | Stationery, toys, trending items |

### Video Layout
```
┌─────────────────┐
│                 │
│  Product image  │  ← Full screen or top 60%
│                 │
├─────────────────┤
│ Caption text    │  ← Character voice playing
│ @worthbuying    │  ← Watermark
└─────────────────┘
```

### What Carries Over From Mr. Oldverdict (65-70%)
- Cloudflare Workers architecture
- Supabase schema (add concept column)
- Render assembly service (modified layout)
- ElevenLabs voice worker (8 voice IDs instead of 1)
- Orchestration worker pattern
- YouTube + Instagram publish workers (shared)

### What Is New
- Product worker — replaces ingestion. Pulls from Amazon/Flipkart affiliate APIs daily.
- Script worker — replaces council. Routes to 1 of 8 character voices. Product-aware prompts.
- Image worker — downloads product images from affiliate URLs. No generation needed.
- Assembly layout — product image prominent. No character image.

### Folder Structure
```
worthbuying/
├── product-worker/src/index.js       # Pulls products from affiliate APIs
├── script-worker/src/index.js        # Generates script in character voice
├── voice-worker/src/index.js         # ElevenLabs — 8 voice IDs
├── assembly-service/app.py           # Product image layout. Modified from Mr. Oldverdict.
├── orchestration-worker/src/index.js # Same pattern as Mr. Oldverdict
└── assets/
    ├── outro-bg.jpg
    └── logo.png
```

### Cost (Additional — on top of existing $15/month)
| Service | Cost | Notes |
|---------|------|-------|
| ElevenLabs | $0 extra | Already on Starter. 8 library voices included. |
| Leonardo | $0 | Not needed — product images from affiliate feed |
| Render | $0 | Second free service |
| Cloudflare | $0 | May need second account for cron slots |
| Affiliate APIs | $0 | Amazon Associates + Flipkart — free after approval |
| **Additional total** | **~₹500-800/month** | Mostly Claude/GPT API for script generation |

### Affiliate API Flag
Amazon Associates and Flipkart both require application and approval. They want to see an active channel or website with existing traffic before granting API access. Apply now — approval takes 2-4 weeks. Pipeline will be ready before approvals come through if applications are submitted early.

### Sequencing
Do not start building until:
1. Mr. Oldverdict hits 30 days consistent posting
2. Google account restored and YouTube pipeline stable
3. Instagram publish live for Mr. Oldverdict
4. Character consistency (init_image_id) solved for Mr. Oldverdict

Start affiliate API applications immediately — they run in parallel with the above.

---

## 27. LIP SYNC UPGRADE — MR. OLDVERDICT

### What It Is
Replace static character image with a talking avatar. Mr. Oldverdict's mouth moves in sync with his voice. More human. More watchable. Matches the character — stillness with just the mouth moving fits his personality perfectly.

### Trigger
Build this when channel hits 1000 subscribers or consistent daily views justify the cost. Not before.

### Options

| Option | Cost | Quality | API | Notes |
|--------|------|---------|-----|-------|
| D-ID | $5.90/month | Good | Yes | Best fit. Send image + audio, get lip-synced video back. Drop-in replacement. |
| HeyGen | $29/month | Best | Yes | Highest quality but expensive for early stage. |
| Hedra | ~$10/month | Good | Beta | Newer platform. Worth watching. |
| Kling AI | Competitive | Very good | Yes | Chinese platform. Good quality. |
| Wav2Lip | Free | Decent | Self-hosted | Open source. Needs GPU. Render free tier is CPU — would be very slow. |
| SadTalker | Free | Better than Wav2Lip | Self-hosted | Open source. Better head movement. Same GPU problem. |

### Recommended Path
**D-ID at $5.90/month.** Clean API. CPU-friendly. Drop-in replacement for current image worker.

### Pipeline Change
Current: Image worker → generates still image → assembly uses as background
After: Lip sync worker → sends reference image + audio to D-ID → receives video clip → assembly composites around it

Reference image: Already locked. Script ID 94dee31e. Use this as D-ID source image.

### Impact on WorthBuying
Not applicable — WorthBuying shows no character faces.

---

## 28. TOPIC INGESTION EXPANSION

### Current State
Ingestion worker pulls only from Reddit. 5 subreddits mapped to 5 categories. Works for now. Becomes a problem after 60 days when topics start cycling.

### Sources To Add
| Source | Type | Category Fit | Effort |
|--------|------|-------------|--------|
| Google Trends | Trending searches | A, D | Low — free API |
| X/Twitter trending | Real-time trends | A, B | Medium — API cost |
| News headlines | BBC, Guardian, TOI English | A, B, C, D | Low — RSS feeds, free |
| Quora | Most upvoted questions | A, C, D | Medium — scraping |
| LinkedIn trending | Professional content | B | Medium — API limited |
| YouTube comments | Viral Shorts comments | A, C | Medium — YouTube Data API |
| Hacker News | Front page | B, D, E | Low — free API |
| Product Hunt | New launches | E | Low — free API |

### Priority Order
1. Google Trends — free, easy, gives UK and Australia signal beyond Reddit's US skew
2. News RSS feeds — free, zero API cost, broad coverage
3. Hacker News — free API, good for Category B and E
4. X/Twitter — useful but API now costs money. Do last.

### When To Build
After 60 days of posting or when topics queue drops below 20 unused topics consistently.

---

## 29. CHANNEL ROADMAP

### Mr. Oldverdict
| Milestone | Target | Action |
|-----------|--------|--------|
| First video live | ✅ March 1 2026 | Done |
| 10 buffer videos | ✅ Done | Publish 2/day manually until pipeline takes over |
| Instagram live | Next session | Build Graph API publish route |
| 100 subscribers | Day 30-45 | Organic. No action needed. |
| Lip sync upgrade | 1000 subscribers | Switch to D-ID |
| 4 videos/day | When channel earns | Scale orchestration crons |

### WorthBuying
| Milestone | Target | Action |
|-----------|--------|--------|
| Affiliate applications | This week | Amazon Associates + Flipkart |
| Build start | Day 30 of Mr. Oldverdict | After pipeline is stable |
| First video | Day 60 | Pending affiliate approval |
| Revenue start | Day 1 of posting | Affiliate commissions on every video |
