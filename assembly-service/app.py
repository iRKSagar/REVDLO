import PIL.Image
from PIL import ImageDraw
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os
import re
import time
import numpy as np
import requests
import tempfile
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify
from moviepy.editor import (
    ImageClip, VideoClip, AudioFileClip, CompositeVideoClip, TextClip
)
from moviepy.video.fx.all import crop
from moviepy.audio.AudioClip import AudioClip, concatenate_audioclips

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    return response

@app.route('/', methods=['OPTIONS'])
@app.route('/assemble', methods=['OPTIONS'])
@app.route('/publish', methods=['OPTIONS'])
@app.route('/publish-instagram', methods=['OPTIONS'])
@app.route('/run-pipeline', methods=['OPTIONS'])
def options_handler():
    return '', 204

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
COUNCIL_SECRET = os.environ.get('COUNCIL_SECRET')

COUNCIL_URL = 'https://revdlo1.rkinfoarch.workers.dev/'
VOICE_URL = 'https://voice.rkinfoarch.workers.dev/'
IMAGE_URL = 'https://image.rkinfoarch.workers.dev/'
BEARER = 'mroldverdict_xK9mP1978'

YT_CLIENT_ID = os.environ.get('YT_CLIENT_ID')
YT_CLIENT_SECRET = os.environ.get('YT_CLIENT_SECRET')
YT_REFRESH_TOKEN = os.environ.get('YT_REFRESH_TOKEN')

IG_ACCESS_TOKEN = os.environ.get('IG_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.environ.get('IG_ACCOUNT_ID')

INSTAGRAM_HASHTAGS = '#mroldverdict #shorts #comedy #wisdom #observations'


def check_auth(req):
    auth = req.headers.get('Authorization', '')
    return auth == f'Bearer {COUNCIL_SECRET}'



# ─── Leather panel renderer (uses real leather texture image) ─────────────────

def render_leather_panel(video_width, panel_h, leather_path):
    """Load real leather texture, darken center for text readability,
    keep ornate border/corners fully visible. Returns numpy RGBA array."""
    try:
        print(f'[leather panel] loading from {leather_path}')
        src = PIL.Image.open(leather_path).convert('RGBA')
        panel_img = src.resize((video_width, panel_h), PIL.Image.LANCZOS)
        print(f'[leather panel] source size: {src.size}, resized to: {panel_img.size}')

        overlay = PIL.Image.new('RGBA', (video_width, panel_h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)

        border_w = 44
        cx0, cy0 = border_w, border_w
        cx1, cy1 = video_width - border_w, panel_h - border_w

        # Solid dark center for text readability
        od.rectangle([cx0, cy0, cx1, cy1], fill=(0, 0, 0, 190))

        # Feathered gradient from center edge to border — soft blend
        for i in range(20):
            a = int(190 * (1 - i / 20) ** 0.5)
            od.rectangle([cx0 - i, cy0 - i, cx1 + i, cy1 + i], outline=(0, 0, 0, a))

        panel_final = PIL.Image.alpha_composite(panel_img, overlay)
        return np.array(panel_final.convert('RGB'))
    except Exception as e:
        print(f'[leather panel] render failed: {e}')
        return None

# ─── Static zoom (Ken Burns removed — clip.fl breaks compositing on Render CPU) ─
# Animated zoom will be revisited once image rendering is confirmed stable.
# For now: bake a 1.08x static zoom into the crop so face is tight on screen.
# No time-varying transforms. No fl(). Pure ImageClip → crop pipeline.
# (Nothing to call here — zoom is baked into assemble_video crop step below.)


# ─── YouTube helpers ───────────────────────────────────────────────────────────

def get_youtube_access_token():
    res = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': YT_CLIENT_ID,
        'client_secret': YT_CLIENT_SECRET,
        'refresh_token': YT_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    })
    res.raise_for_status()
    return res.json()['access_token']


def upload_to_youtube(video_path, title, description, tags):
    access_token = get_youtube_access_token()
    print(f'[Publish] Access token obtained: {access_token[:20]}...')

    metadata = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': tags,
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    file_size = os.path.getsize(video_path)
    init_res = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Upload-Content-Type': 'video/mp4',
            'X-Upload-Content-Length': str(file_size)
        },
        json=metadata
    )
    init_res.raise_for_status()
    upload_url = init_res.headers['Location']

    with open(video_path, 'rb') as f:
        video_data = f.read()

    upload_res = requests.put(
        upload_url,
        headers={'Content-Type': 'video/mp4', 'Content-Length': str(file_size)},
        data=video_data,
        timeout=300
    )
    upload_res.raise_for_status()
    return upload_res.json().get('id')


def mark_script_published(script_id, youtube_video_id):
    from datetime import datetime, timezone
    requests.patch(
        f'{SUPABASE_URL}/rest/v1/scripts?id=eq.{script_id}',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'published': True,
            'published_at': datetime.now(timezone.utc).isoformat(),
            'youtube_video_id': youtube_video_id
        }
    )


def publish_to_youtube_job(script_id):
    video_path = None
    try:
        print(f'[Publish] Starting YouTube publish for script {script_id}')
        video_record = get_video_record(script_id)
        video_url = video_record.get('video_url')
        if not video_url:
            print(f'[Publish] No video_url found for script {script_id}')
            return

        script = get_script(script_id)
        setup = script.get('setup', 'Mr. Oldverdict')
        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)

        title = setup[:93] + ' #Shorts'
        line1 = strip_emotion_tags(lines[0]['text']) if lines else ''
        line2 = lines[1]['text'] if len(lines) > 1 else ''

        # Build topic-specific hashtags from theme_tags
        theme_tags = script.get('theme_tags', [])
        if isinstance(theme_tags, str):
            import json as _json
            theme_tags = _json.loads(theme_tags)
        topic_hashtags = ' '.join(f'#{t.replace(" ", "")}' for t in theme_tags if t)
        base_hashtags = '#mroldverdict #Shorts #comedy #wisdom #observations'
        all_hashtags = f'{base_hashtags} {topic_hashtags}'.strip()

        description = f'{line1}\n\n{line2}\n\n{all_hashtags}'
        tags = ['mroldverdict', 'shorts', 'comedy', 'wisdom', 'observations', 'oldverdict'] + [t.replace(' ', '') for t in theme_tags if t]

        video_path = download_file(video_url, '.mp4')
        yt_id = upload_to_youtube(video_path, title, description, tags)
        print(f'[Publish] YouTube video ID: {yt_id}')
        mark_script_published(script_id, yt_id)
        print(f'[Publish] Done. https://youtube.com/shorts/{yt_id}')

    except Exception as e:
        import traceback
        print(f'[Publish] Error: {e}')
        print(traceback.format_exc())
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
            except Exception:
                pass


# ─── Instagram helpers ─────────────────────────────────────────────────────────

def build_instagram_caption(script_row):
    lines = script_row.get('lines', [])
    if isinstance(lines, str):
        lines = json.loads(lines)
    if len(lines) >= 2:
        raw = lines[1].get('text', '')
    else:
        raw = script_row.get('setup', '')
    clean = re.sub(r'^\[[^\]]+\]\s*', '', raw).strip()
    # Add topic-specific hashtags from theme_tags
    theme_tags = script_row.get('theme_tags', [])
    if isinstance(theme_tags, str):
        import json as _json
        theme_tags = _json.loads(theme_tags)
    topic_hashtags = ' '.join(f'#{t.replace(" ", "")}' for t in theme_tags if t)
    all_hashtags = f'{INSTAGRAM_HASHTAGS} {topic_hashtags}'.strip()

    return f'{clean}\n\n{all_hashtags}'


def publish_reel_to_instagram(video_public_url, caption):
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        raise ValueError('IG_ACCESS_TOKEN or IG_ACCOUNT_ID not set in environment')

    base = f'https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}'

    container_resp = requests.post(
        f'{base}/media',
        data={
            'media_type': 'REELS',
            'video_url': video_public_url,
            'caption': caption,
            'share_to_feed': 'true',
            'access_token': IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    container_data = container_resp.json()
    if 'id' not in container_data:
        raise RuntimeError(f'Container creation failed: {container_data}')

    creation_id = container_data['id']
    print(f'[Instagram] Container created: {creation_id}')

    for attempt in range(30):
        time.sleep(10)
        status_resp = requests.get(
            f'https://graph.facebook.com/v19.0/{creation_id}',
            params={'fields': 'status_code', 'access_token': IG_ACCESS_TOKEN},
            timeout=30,
        )
        status_data = status_resp.json()
        status_code = status_data.get('status_code', '')
        print(f'[Instagram] Container status ({attempt + 1}/30): {status_code}')
        if status_code == 'FINISHED':
            break
        if status_code == 'ERROR':
            raise RuntimeError(f'Container processing error: {status_data}')
    else:
        raise RuntimeError('Container did not finish processing within 5 minutes')

    publish_resp = requests.post(
        f'{base}/media_publish',
        data={'creation_id': creation_id, 'access_token': IG_ACCESS_TOKEN},
        timeout=60,
    )
    publish_data = publish_resp.json()
    if 'id' not in publish_data:
        raise RuntimeError(f'Publish failed: {publish_data}')

    media_id = publish_data['id']
    print(f'[Instagram] Published Reel: {media_id}')
    return media_id


def mark_script_instagram_published(script_id, instagram_media_id):
    requests.patch(
        f'{SUPABASE_URL}/rest/v1/scripts?id=eq.{script_id}',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        },
        json={'instagram_media_id': instagram_media_id}
    )


def publish_to_instagram_job(script_id):
    video_path = None
    try:
        print(f'[Instagram] Starting publish for script {script_id}')
        video_record = get_video_record(script_id)
        video_url = video_record.get('video_url')
        if not video_url:
            print(f'[Instagram] No video_url for script {script_id}')
            return None

        script = get_script(script_id)
        caption = build_instagram_caption(script)
        print(f'[Instagram] Caption: {caption[:80]}...')

        media_id = publish_reel_to_instagram(video_url, caption)
        mark_script_instagram_published(script_id, media_id)
        print(f'[Instagram] Done. Media ID: {media_id}')
        return media_id

    except Exception as e:
        import traceback
        print(f'[Instagram] Error: {e}')
        print(traceback.format_exc())
        return None
    finally:
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
            except Exception:
                pass


# ─── Shared helpers ────────────────────────────────────────────────────────────

def download_file(url, suffix):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(response.content)
    tmp.close()
    return tmp.name


def get_video_record(script_id):
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/videos?script_id=eq.{script_id}&limit=1',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception('No video record found for this script')
    return data[0]


def get_script(script_id):
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/scripts?id=eq.{script_id}&limit=1&select=id,setup,lines,scene,prop,expression,theme_tags',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception('Script not found')
    row = data[0]
    print(f"Raw script row: {row}")
    return row


def strip_emotion_tags(text):
    return re.sub(r'\[.*?\]', '', text).strip()


# ─── Setup card (full brightness face, static text) ─────────────────────────

def build_setup_card(setup_text, video_width, video_height, image_path=None,
                     duration=5.0, typewriter_sound_path=None, logo_path=None, leather_panel_path=None):
    """Full brightness face. Setup text on leather panel at bottom — same visual
    language as main clip captions. Silent. No animation. No floating band."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, ImageClip

        if image_path and os.path.exists(image_path):
            pil_bg = PIL.Image.open(image_path).convert('RGB')
            img_w, img_h = pil_bg.size
            scale = max(video_width / img_w, video_height / img_h) * 1.2
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            pil_bg = pil_bg.resize((new_w, new_h), PIL.Image.LANCZOS)
            x0 = (new_w - video_width) // 2
            y0 = int(new_h * 0.38) - video_height // 2
            y0 = max(0, min(y0, new_h - video_height))
            x0 = max(0, min(x0, new_w - video_width))
            pil_bg = pil_bg.crop((x0, y0, x0 + video_width, y0 + video_height))
            bg_base = ImageClip(np.array(pil_bg))
        else:
            bg_base = ColorClip(size=(video_width, video_height), color=(15, 15, 15))

        bg_clip = bg_base.set_duration(duration)

        # ── Leather panel — real texture same as main clip ─────────────────
        panel_h = 310
        panel_y = video_height - panel_h

        if leather_panel_path and os.path.exists(leather_panel_path):
            arr = render_leather_panel(video_width, panel_h, leather_panel_path)
            if arr is not None:
                from moviepy.editor import ImageClip as _IC
                leather_clips = [(_IC(arr).set_position((0, panel_y)).set_duration(duration))]
            else:
                leather_clips = [(ColorClip(size=(video_width, panel_h), color=(20,10,5))
                                  .set_opacity(0.85).set_position((0, panel_y)).set_duration(duration))]
        else:
            leather_clips = [(ColorClip(size=(video_width, panel_h), color=(20,10,5))
                              .set_opacity(0.85).set_position((0, panel_y)).set_duration(duration))]

        # Setup text — sits inside the panel
        text_y = panel_y + 43
        txt_clip = (TextClip(
            setup_text,
            fontsize=34,
            color='white',
            font='DejaVu-Serif-Bold',
            method='caption',
            size=(video_width - 80, None),
            stroke_color='black',
            stroke_width=3,
            align='center'
        )
        .set_position(('center', text_y))
        .set_duration(duration))

        logo_clips = []
        if logo_path and os.path.exists(logo_path):
            try:
                logo_img = (ImageClip(logo_path)
                            .resize(height=70)
                            .set_position((24, 24))
                            .set_duration(duration))
                logo_clips = [logo_img]
            except Exception as e:
                print(f'Logo on setup card failed: {e}')

        all_clips = [bg_clip] + leather_clips + logo_clips + [txt_clip]
        card = CompositeVideoClip(all_clips, size=(video_width, video_height)).set_duration(duration)
        return card

    except Exception as e:
        print(f'Setup card failed: {e}')
        return None


# ─── Caption layer with leather panel + HUD ───────────────────────────────────

def build_caption_panel(video_width, video_height, duration, leather_path=None):
    """Real leather texture panel — ornate corners, stitched border, dark center.
    Falls back to solid dark panel if leather image not available."""
    from moviepy.editor import ColorClip, ImageClip

    panel_h = 310
    panel_y = video_height - panel_h

    if leather_path and os.path.exists(leather_path):
        arr = render_leather_panel(video_width, panel_h, leather_path)
        if arr is not None:
            panel_clip = (ImageClip(arr)
                          .set_position((0, panel_y))
                          .set_duration(duration))
            return [panel_clip]

    # Fallback — solid dark panel
    base = (ColorClip(size=(video_width, panel_h), color=(20, 10, 5))
            .set_opacity(0.85)
            .set_position((0, panel_y))
            .set_duration(duration))
    return [base]


def build_caption_clips(setup_text, lines, voice_duration, video_width, video_height):
    """Captions for setup text + line 1 + line 2, synced to voice duration.
    Setup text gets 1.65x weight (pause_after). All captions sit inside leather panel."""
    caption_clips = []

    all_items = []
    if setup_text:
        all_items.append({'text': setup_text, 'pause_after': True})
    for line in lines:
        all_items.append(line)

    if not all_items:
        return caption_clips

    cleaned = [strip_emotion_tags(item.get('text', '')) for item in all_items]
    char_counts = [max(len(t), 1) for t in cleaned]

    weights = []
    for i, item in enumerate(all_items):
        w = char_counts[i]
        if item.get('pause_after', False):
            w *= 1.65
        weights.append(w)
    total_weight = sum(weights)

    panel_h = 310
    panel_y = video_height - panel_h
    text_y = panel_y + 43  # 20% walked back down

    current_time = 0
    for i, item in enumerate(all_items):
        text = cleaned[i]
        if not text:
            current_time += (weights[i] / total_weight) * voice_duration
            continue

        duration = (weights[i] / total_weight) * voice_duration
        duration = min(duration, voice_duration - current_time)
        if duration <= 0:
            break

        try:
            txt_clip = (TextClip(
                text,
                fontsize=34,
                color='white',
                font='DejaVu-Serif-Bold',
                method='caption',
                size=(video_width - 80, None),
                stroke_color='black',
                stroke_width=3,
                align='center'
            )
            .set_position(('center', text_y))
            .set_start(current_time)
            .set_duration(duration))
            caption_clips.append(txt_clip)
        except Exception as e:
            print(f'Caption generation failed for item {i}: {e}')

        current_time += duration

    return caption_clips


def get_outro_sound_url(supabase_url, supabase_key):
    try:
        response = requests.get(
            f'{supabase_url}/rest/v1/settings?key=eq.outro_sound_url&limit=1',
            headers={'apikey': supabase_key, 'Authorization': f'Bearer {supabase_key}'}
        )
        data = response.json()
        if data and data[0].get('value') and data[0]['value'] != 'PLACEHOLDER':
            return data[0]['value']
    except Exception as e:
        print(f'Failed to fetch outro sound URL: {e}')
    return None


def get_setting(supabase_url, supabase_key, key):
    try:
        response = requests.get(
            f'{supabase_url}/rest/v1/settings?key=eq.{key}&limit=1',
            headers={'apikey': supabase_key, 'Authorization': f'Bearer {supabase_key}'}
        )
        data = response.json()
        if data and data[0].get('value'):
            return data[0]['value']
    except Exception as e:
        print(f'Failed to fetch setting {key}: {e}')
    return None


def build_outro_card(video_width, video_height, outro_audio_path=None,
                     duration=3.0, image_path=None, logo_path=None):
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip, ImageClip

        if image_path and os.path.exists(image_path):
            bg_img = ImageClip(image_path).resize((video_width, video_height)).set_duration(duration)
            dark_overlay = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).set_opacity(0.75).set_duration(duration)
            bg = CompositeVideoClip([bg_img, dark_overlay], size=(video_width, video_height))
        else:
            bg = ColorClip(size=(video_width, video_height), color=(10, 10, 10)).set_duration(duration)

        name_clip = (TextClip("Mr. Oldverdict", fontsize=58, color='white', font='DejaVu-Serif-Bold', method='label', align='center')
                     .set_position(('center', video_height * 0.38)).set_duration(duration))
        tagline_clip = (TextClip("Been watching since before.", fontsize=32, color='#aaaaaa', font='DejaVu-Serif', method='label', align='center')
                        .set_position(('center', video_height * 0.50)).set_duration(duration))
        follow_clip = (TextClip("Your daily dose of old wisdom.", fontsize=26, color='#aaaaaa', font='DejaVu-Serif', method='label', align='center')
                       .set_position(('center', video_height * 0.63)).set_duration(duration))
        follow2_clip = (TextClip("Follow @mroldverdict", fontsize=24, color='#888888', font='DejaVu-Serif', method='label', align='center')
                        .set_position(('center', video_height * 0.70)).set_duration(duration))

        outro_layers = [bg, name_clip, tagline_clip, follow_clip, follow2_clip]

        if logo_path and os.path.exists(logo_path):
            try:
                outro_logo = ImageClip(logo_path).resize(height=70).set_position((24, 24)).set_duration(duration)
                outro_layers.append(outro_logo)
            except Exception as e:
                print(f'Logo on outro failed: {e}')

        outro = CompositeVideoClip(outro_layers, size=(video_width, video_height))

        if outro_audio_path and os.path.exists(outro_audio_path):
            try:
                outro_audio = AudioFileClip(outro_audio_path).subclip(0, min(duration, AudioFileClip(outro_audio_path).duration))
                outro = outro.set_audio(outro_audio)
            except Exception as e:
                print(f'Outro audio failed: {e}')

        return outro
    except Exception as e:
        print(f'Outro card failed: {e}')
        return None


# ─── Main assembly ─────────────────────────────────────────────────────────────

def assemble_video(image_path, audio_path, lines, output_path, setup_text=None,
                   outro_sound_path=None, typewriter_sound_path=None,
                   outro_bg_path=None, logo_path=None, leather_panel_path=None):
    """
    Video structure:
    1. Setup card — full brightness face, static text, logo (5s) → fade out 0.8s
    2. Main clip — face fades in 0.3s, voice starts immediately
       - Leather/HUD panel with captions: setup text → line 1 → line 2
       - Ken Burns slow zoom 1.0x → 1.08x throughout
       - Panel and captions disappear when voice ends
    3. Post-voice hold — 2.2s clean face, no panel, zoom continues
    4. Fade to black 0.6s + 1.5s black gap
    5. Outro card — 3.5s, fades in 0.5s
    """
    audio = AudioFileClip(audio_path)
    voice_duration = audio.duration

    target_width = 540
    target_height = 960

    # ── Load original image in PIL — keep full res for zoom math ───────────────
    pil_orig = PIL.Image.open(image_path).convert('RGB')
    img_w, img_h = pil_orig.size
    base_scale = max(target_width / img_w, target_height / img_h) * 1.2

    # ── Total main clip duration: voice + clean hold ─────────────────────────
    post_hold = 2.2
    total_duration = voice_duration + post_hold

    # ── Ken Burns: slow zoom 1.0x → 1.08x over total_duration ───────────────
    # Per-frame PIL resize+crop. BILINEAR used (faster than LANCZOS, imperceptible
    # difference at short durations). ~480 frames at 24fps, ~2ms each on Render.
    def make_frame(t):
        progress = min(t / total_duration, 1.0)
        zoom = 1.0 + 0.08 * progress          # 1.00 → 1.08
        scale = base_scale * zoom
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        frame = pil_orig.resize((new_w, new_h), PIL.Image.BILINEAR)
        x0 = (new_w - target_width) // 2
        y0 = int(new_h * 0.38) - target_height // 2
        y0 = max(0, min(y0, new_h - target_height))
        x0 = max(0, min(x0, new_w - target_width))
        frame = frame.crop((x0, y0, x0 + target_width, y0 + target_height))
        return np.array(frame)

    image_clip = VideoClip(make_frame, duration=total_duration)

    # ── Leather panel + HUD — only during voice, not during hold ────────────
    panel_layers = build_caption_panel(target_width, target_height, voice_duration, leather_path=leather_panel_path)

    # ── Captions: setup text → line 1 → line 2 ──────────────────────────────
    # Setup text is first caption, then line 1, then line 2
    caption_clips = build_caption_clips(setup_text, lines, voice_duration, target_width, target_height)

    # ── Compose main layers (no watermark) ──────────────────────────────────
    main_layers = [image_clip] + panel_layers + caption_clips

    # ── Audio: voice starts at frame 1, silence for post hold ────────────────
    audio_faded = audio.audio_fadein(0.3).audio_fadeout(0.5)
    silence_post = AudioClip(lambda t: np.zeros(2), duration=post_hold, fps=44100)
    extended_audio = concatenate_audioclips([audio_faded, silence_post])

    main_clip = CompositeVideoClip(main_layers, size=(target_width, target_height))
    main_clip = main_clip.fadein(0.3).set_audio(extended_audio).set_duration(total_duration).fadeout(0.6)

    # ── Full assembly ────────────────────────────────────────────────────────
    from moviepy.editor import concatenate_videoclips, ColorClip as _ColorClip

    clips = []

    # No separate setup card — voice starts from frame 1.
    # Setup text is the first caption on the leather panel.
    clips.append(main_clip)

    fade_gap = _ColorClip(size=(target_width, target_height), color=(0, 0, 0)).set_duration(1.5)
    clips.append(fade_gap)

    outro_card = build_outro_card(
        target_width, target_height,
        outro_audio_path=outro_sound_path,
        duration=3.5,
        image_path=outro_bg_path,
        logo_path=logo_path
    )
    if outro_card:
        outro_card = outro_card.fadein(0.5)
        clips.append(outro_card)

    final = concatenate_videoclips(clips) if len(clips) > 1 else main_clip

    final.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile=output_path + '_temp_audio.m4a',
        remove_temp=True,
        preset='ultrafast',
        ffmpeg_params=['-crf', '28']
    )

    audio.close()
    final.close()


def upload_video(script_id, video_path):
    with open(video_path, 'rb') as f:
        video_data = f.read()

    file_name = f'videos/{script_id}.mp4'
    response = requests.post(
        f'{SUPABASE_URL}/storage/v1/object/revdlo-media/{file_name}',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'video/mp4',
            'Cache-Control': '3600',
            'x-upsert': 'true'
        },
        data=video_data,
        timeout=120
    )
    if not response.ok:
        raise Exception(f'Video upload failed: {response.text}')
    return f'{SUPABASE_URL}/storage/v1/object/public/revdlo-media/{file_name}'


def update_video_record(script_id, video_url):
    requests.patch(
        f'{SUPABASE_URL}/rest/v1/videos?script_id=eq.{script_id}',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json'
        },
        json={'video_url': video_url}
    )


def run_pipeline_job():
    print('[Pipeline] Starting automated pipeline run...')

    image_path = audio_path = output_path = None
    outro_sound_path = typewriter_sound_path = outro_bg_path = logo_path = None

    try:
        print('[Pipeline] Step 1: Calling council worker...')
        council_res = requests.post(
            COUNCIL_URL,
            headers={'Authorization': f'Bearer {BEARER}', 'Content-Type': 'application/json'},
            json={}, timeout=60
        )
        council_res.raise_for_status()
        council_data = council_res.json()
        script_id = council_data.get('script_id')

        if not script_id:
            print(f'[Pipeline] Council failed: {council_data}')
            return

        print(f'[Pipeline] Script generated: {script_id}')

        print('[Pipeline] Step 2: Calling voice and image workers simultaneously...')

        def call_voice():
            res = requests.post(VOICE_URL,
                                headers={'Authorization': f'Bearer {BEARER}', 'Content-Type': 'application/json'},
                                json={'script_id': script_id}, timeout=120)
            return ('voice', res.status_code, res.text)

        def call_image():
            res = requests.post(IMAGE_URL,
                                headers={'Authorization': f'Bearer {BEARER}', 'Content-Type': 'application/json'},
                                json={'script_id': script_id}, timeout=120)
            return ('image', res.status_code, res.text)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(call_voice), executor.submit(call_image)]
            for future in as_completed(futures):
                label, status, body = future.result()
                print(f'[Pipeline] {label} worker: {status} - {body[:200]}')

        print('[Pipeline] Step 3: Polling for voice and image completion...')
        max_wait, poll_interval, elapsed = 300, 10, 0
        voice_ready = image_ready = False

        while elapsed < max_wait:
            try:
                rec = get_video_record(script_id)
                voice_ready = bool(rec.get('voice_file_url'))
                image_ready = bool(rec.get('image_url'))
                print(f'[Pipeline] Poll {elapsed}s - voice: {voice_ready}, image: {image_ready}')
                if voice_ready and image_ready:
                    break
            except Exception as e:
                print(f'[Pipeline] Poll error: {e}')
            time.sleep(poll_interval)
            elapsed += poll_interval

        if not voice_ready or not image_ready:
            print(f'[Pipeline] Timeout. voice: {voice_ready}, image: {image_ready}')
            return

        print('[Pipeline] Step 4: Assembling video...')
        video_record = get_video_record(script_id)
        script = get_script(script_id)

        outro_sound_url = get_outro_sound_url(SUPABASE_URL, SUPABASE_KEY)
        # typewriter_sound_url no longer used — sound removed
        outro_bg_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'outro_bg_url')
        logo_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'logo_url')

        image_url = video_record.get('image_url')
        audio_url = video_record.get('voice_file_url')

        image_path = download_file(image_url, '.jpg')
        audio_path = download_file(audio_url, '.mp3')

        if outro_sound_url:
            try:
                outro_sound_path = download_file(outro_sound_url, '.mp3')
            except Exception as e:
                print(f'[Pipeline] Outro sound download failed: {e}')



        if outro_bg_url:
            try:
                outro_bg_path = download_file(outro_bg_url, '.jpg')
            except Exception as e:
                print(f'[Pipeline] Outro bg download failed: {e}')

        if logo_url:
            try:
                logo_path = download_file(logo_url, '.png')
            except Exception as e:
                print(f'[Pipeline] Logo download failed: {e}')

        leather_panel_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'leather_panel_url')
        leather_panel_path = None
        if leather_panel_url:
            try:
                leather_panel_path = download_file(leather_panel_url, '.png')
                print(f'[Pipeline] Leather panel downloaded')
            except Exception as e:
                print(f'[Pipeline] Leather panel download failed: {e}')

        output_path = tempfile.mktemp(suffix='.mp4')

        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)
        setup_text = script.get('setup', None)

        assemble_video(image_path, audio_path, lines, output_path, setup_text,
                       outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path,
                       leather_panel_path=leather_panel_path)

        video_url = upload_video(script_id, output_path)
        update_video_record(script_id, video_url)
        print(f'[Pipeline] Done. Video URL: {video_url}')

        if YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN:
            print('[Pipeline] Step 5: Publishing to YouTube...')
            publish_to_youtube_job(script_id)
        else:
            print('[Pipeline] YouTube credentials not set. Skipping.')

        if IG_ACCESS_TOKEN and IG_ACCOUNT_ID:
            print('[Pipeline] Step 6: Publishing to Instagram...')
            ig_media_id = publish_to_instagram_job(script_id)
            if ig_media_id:
                print(f'[Pipeline] Instagram published: {ig_media_id}')
        else:
            print('[Pipeline] Instagram credentials not set. Skipping.')

    except Exception as e:
        import traceback
        print(f'[Pipeline] Error: {e}')
        print(traceback.format_exc())
    finally:
        for path in [image_path, audio_path, output_path, outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'Assembly service standing by.'})


@app.route('/run-pipeline', methods=['POST'])
def run_pipeline():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    thread = threading.Thread(target=run_pipeline_job, daemon=True)
    thread.start()
    return jsonify({
        'status': 'Pipeline started',
        'message': 'Council → Voice + Image → Assembly → YouTube → Instagram running in background'
    }), 202


@app.route('/publish', methods=['POST'])
def publish():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400
    publish_to_youtube_job(script_id)
    return jsonify({'status': 'Publish complete', 'script_id': script_id}), 200


@app.route('/publish-instagram', methods=['POST'])
def publish_instagram():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        return jsonify({'error': 'IG_ACCESS_TOKEN or IG_ACCOUNT_ID not set'}), 500
    media_id = publish_to_instagram_job(script_id)
    if media_id:
        return jsonify({'success': True, 'media_id': media_id, 'script_id': script_id}), 200
    return jsonify({'success': False, 'error': 'Instagram publish failed', 'script_id': script_id}), 500


def assemble_job(script_id):
    """Background thread: assembles video and auto-publishes to YouTube."""
    image_path = audio_path = output_path = None
    try:
        video_record = get_video_record(script_id)
        script = get_script(script_id)

        outro_sound_url = get_outro_sound_url(SUPABASE_URL, SUPABASE_KEY)
        outro_bg_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'outro_bg_url')
        logo_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'logo_url')

        image_url = video_record.get('image_url')
        audio_url = video_record.get('voice_file_url')

        if not image_url:
            print(f"[assemble_job] No image for {script_id}"); return
        if not audio_url:
            print(f"[assemble_job] No audio for {script_id}"); return

        image_path = download_file(image_url, '.jpg')
        audio_path = download_file(audio_url, '.mp3')

        outro_sound_path = None
        if outro_sound_url:
            try: outro_sound_path = download_file(outro_sound_url, '.mp3')
            except Exception as e: print(f'Outro sound download failed: {e}')

        typewriter_sound_path = None

        outro_bg_path = None
        if outro_bg_url:
            try: outro_bg_path = download_file(outro_bg_url, '.jpg')
            except Exception as e: print(f'Outro bg download failed: {e}')

        logo_path = None
        if logo_url:
            try: logo_path = download_file(logo_url, '.png')
            except Exception as e: print(f'Logo download failed: {e}')

        leather_panel_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'leather_panel_url')
        leather_panel_path = None
        if leather_panel_url:
            try: leather_panel_path = download_file(leather_panel_url, '.png')
            except Exception as e: print(f'Leather panel download failed: {e}')

        output_path = tempfile.mktemp(suffix='.mp4')

        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)
        setup_text = script.get('setup', None)

        assemble_video(image_path, audio_path, lines, output_path, setup_text,
                       outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path,
                       leather_panel_path=leather_panel_path)

        video_url = upload_video(script_id, output_path)
        update_video_record(script_id, video_url)
        print(f"[assemble_job] Done: {video_url}")

        publish_to_youtube_job(script_id)

    except Exception as e:
        import traceback
        print(f"[assemble_job] Error: {e}")
        print(traceback.format_exc())
    finally:
        for path in [image_path, audio_path, output_path]:
            if path and os.path.exists(path):
                try: os.unlink(path)
                except Exception: pass


@app.route('/assemble', methods=['POST'])
def assemble():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400
    thread = threading.Thread(target=assemble_job, args=(script_id,), daemon=True)
    thread.start()
    return jsonify({'status': 'Assembly started', 'script_id': script_id,
                    'message': 'Poll Supabase videos table for video_url'}), 202


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
