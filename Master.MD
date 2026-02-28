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

Blacklist keywords in code: trump, biden, obama, modi, putin, xi, sunak, labour, republican, democrat, conservative, liberal, maga, woke, israel, palestine, ukraine, russia, china, christian, muslim, islam, hindu, jewish, bible, quran, torah, apple, google, microsoft, amazon, meta, facebook, instagram, tiktok, twitter, netflix, elon, musk, bezos, zuckerberg, epstein, kardashian

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
| Ingestion | https://ingestion.rkinfoarch.workers.dev/ | Reddit topic ingestion | 1 (6 AM UTC) |
| Voice | https://voice.rkinfoarch.workers.dev/ | ElevenLabs audio | None (POST only) |
| Image | https://image.rkinfoarch.workers.dev/ | Leonardo AI image | None (POST only) |
| Orchestration | https://orchestration.rkinfoarch.workers.dev/ | Full pipeline trigger | 2 (8 PM UTC today, 11 AM UTC tomorrow) |

Note: Cloudflare free tier allows 5 cron triggers maximum. All 5 now used (ingestion + 2 orchestration + 2 council removed).
Orchestration Git build deploy command: `npx wrangler deploy --config wrangler.orchestration.toml`

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

### URGENT — Must do before March 8 2026
- [ ] **OAuth consent screen to Production**: Currently in Testing mode. Refresh token expires in 7 days (March 7). Go to Google Cloud Console → APIs & Services → OAuth consent screen → Publish app → Submit for verification OR switch to Production. If this is not done YouTube publishing stops on March 7.

### Immediate
- [ ] **Publish remaining 9 buffer videos**: Use `/publish` route manually. Script IDs in Section 16. Post 2 per day starting today.
- [ ] **YouTube channel art**: Profile picture and banner for @mroldverdict using reference image.
- [ ] **Character consistency**: Leonardo reference image locking. Try `init_image_id` approach. Upload reference image to Leonardo API, get internal ID, use in generation with strength 0.2-0.3.
- [ ] **Logo regeneration**: Once character reference is locked, regenerate logo123.png using the locked face. Replace in GitHub assets.
- [ ] **Caption sync**: Character count weighting is approximate. True sync requires per-line audio duration from ElevenLabs. ElevenLabs v3 does not return timestamps. Workaround pending.
- [ ] **Cloudflare GitHub PR bot**: Disable in Cloudflare Settings > Git integration for each worker.

### Short Term (next session)
- [ ] **Instagram account**: Create @mroldverdict. Switch to Creator. Link Facebook page.
- [ ] **Instagram publish**: Instagram Graph API. Two step process: create container, then publish. Caption: second line + hashtags. Build after Instagram account is created.
- [ ] **Topics queue**: Load 60+ topics into Supabase topics table for ingestion worker to use.

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
- **Refresh token expires: March 7 2026** (7 days from issue — Testing mode limitation)
- OAuth consent screen status: Testing. Must publish to Production before March 7.

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
