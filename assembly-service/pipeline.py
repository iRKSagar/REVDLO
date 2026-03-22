import modal
import PIL.Image
from PIL import ImageDraw, ImageFont
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os
import re
import time
import subprocess
import tempfile
import json
import threading
import numpy as np
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify

# ── Modal setup ────────────────────────────────────────────────────────────────

modal_app = modal.App('mr-oldverdict')

modal_image = (
    modal.Image.debian_slim(python_version='3.11')
    .apt_install(
        'ffmpeg',
        'fonts-dejavu-core',
        'fonts-dejavu-extra',
        'fonts-liberation',
        'fonts-noto'
    )
    .pip_install(
        'flask',
        'requests',
        'pillow',
        'numpy'
    )
)

secrets = [modal.Secret.from_name('mr-oldverdict-secrets')]

# ── Flask app ──────────────────────────────────────────────────────────────────

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
@app.route('/video-status', methods=['OPTIONS'])
@app.route('/videos/incomplete', methods=['OPTIONS'])
def options_handler():
    return '', 204

# ── Config ─────────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
COUNCIL_SECRET = os.environ.get('COUNCIL_SECRET')

COUNCIL_URL = 'https://revdlo1.rkinfoarch.workers.dev/'
VOICE_URL   = 'https://voice.rkinfoarch.workers.dev/'
IMAGE_URL   = 'https://image.rkinfoarch.workers.dev/'
BEARER      = 'mroldverdict_xK9mP1978'

YT_CLIENT_ID     = os.environ.get('YT_CLIENT_ID')
YT_CLIENT_SECRET = os.environ.get('YT_CLIENT_SECRET')
YT_REFRESH_TOKEN = os.environ.get('YT_REFRESH_TOKEN')

IG_ACCESS_TOKEN = os.environ.get('IG_ACCESS_TOKEN')
IG_ACCOUNT_ID   = os.environ.get('IG_ACCOUNT_ID')

INSTAGRAM_HASHTAGS = '#mroldverdict #shorts #comedy #wisdom #observations'

VIDEO_W   = 540
VIDEO_H   = 960
BAR_H     = 90          # letterbox bar height (top and bottom)
BOT_BAR_Y = VIDEO_H - BAR_H   # 870
FPS       = 24

# ── Expression presets ─────────────────────────────────────────────────────────
# eq:    contrast, brightness, saturation — confirmed working on Modal debian ffmpeg
# hue:   h=degrees, s=saturation_scale — confirmed working, no quotes needed
# grain: c0s noise strength (8=subtle, 16=heavy film stock)
# pan:   left | right | still

EXPRESSION_PRESETS = {
    'flat_observation': {
        'eq':    'contrast=1.05:brightness=0.02:saturation=1.1',
        'hue':   'h=3:s=1.1',
        'grain': 8,
        'pan':   'left',
    },
    'slight_raise': {
        'eq':    'contrast=1.08:brightness=0.01:saturation=0.95',
        'hue':   'h=-4:s=1.0',
        'grain': 10,
        'pan':   'right',
    },
    'mid_line_delivery': {
        'eq':    'contrast=1.10:brightness=0.02:saturation=1.05',
        'hue':   'h=0:s=1.0',
        'grain': 12,
        'pan':   'still',
    },
    'quiet_concern': {
        'eq':    'contrast=1.12:brightness=0.01:saturation=0.75',
        'hue':   'h=-8:s=1.0',
        'grain': 16,
        'pan':   'still',
    },
    'precise_destruction': {
        'eq':    'contrast=1.18:brightness=-0.03:saturation=1.2',
        'hue':   'h=6:s=1.1',
        'grain': 14,
        'pan':   'right',
    },
    'faint_amusement': {
        'eq':    'contrast=1.02:brightness=0.02:saturation=1.15',
        'hue':   'h=10:s=1.1',
        'grain': 9,
        'pan':   'left',
    },
}

def get_expression_preset(expression):
    return EXPRESSION_PRESETS.get(
        expression or 'flat_observation',
        EXPRESSION_PRESETS['flat_observation']
    )

# ── Auth ───────────────────────────────────────────────────────────────────────

def check_auth(req):
    auth = req.headers.get('Authorization', '')
    return auth == f'Bearer {COUNCIL_SECRET}'

# ── Shared helpers ─────────────────────────────────────────────────────────────

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
        f'{SUPABASE_URL}/rest/v1/scripts?id=eq.{script_id}&limit=1'
        f'&select=id,setup,lines,scene,prop,expression,theme_tags,pinned_comment',
        headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception('Script not found')
    row = data[0]
    row['expression'] = row.get('expression') or 'flat_observation'
    print(f'[get_script] id={script_id} expression={row["expression"]}')
    return row


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


def strip_emotion_tags(text):
    return re.sub(r'\[.*?\]', '', text).strip()


def upload_video(script_id, video_path):
    with open(video_path, 'rb') as f:
        video_data = f.read()
    file_name = f'videos/{script_id}.mp4'
    response = requests.post(
        f'{SUPABASE_URL}/storage/v1/object/revdlo-media/{file_name}',
        headers={
            'apikey':        SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type':  'video/mp4',
            'Cache-Control': '3600',
            'x-upsert':      'true'
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
            'apikey':        SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type':  'application/json'
        },
        json={'video_url': video_url}
    )

# ── YouTube helpers ────────────────────────────────────────────────────────────

def get_youtube_access_token():
    try:
        print('YT_CLIENT_ID:', YT_CLIENT_ID[:20] if YT_CLIENT_ID else None)
        print('YT_SECRET_PRESENT:', bool(YT_CLIENT_SECRET))
        print('YT_REFRESH:', YT_REFRESH_TOKEN[:10] if YT_REFRESH_TOKEN else None)
        res = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id':     (YT_CLIENT_ID or '').strip(),
                'client_secret': (YT_CLIENT_SECRET or '').strip(),
                'refresh_token': (YT_REFRESH_TOKEN or '').strip(),
                'grant_type':    'refresh_token'
            },
            timeout=30
        )
        print('YT TOKEN RESPONSE:', res.text)
        res.raise_for_status()
        return res.json()['access_token']
    except Exception as e:
        print('YouTube token fetch failed:', e)
        raise


def upload_to_youtube(video_path, title, description, tags):
    access_token = get_youtube_access_token()
    print(f'[Publish] Access token obtained: {access_token[:20]}...')
    metadata = {
        'snippet': {
            'title':       title[:100],
            'description': description,
            'tags':        tags,
            'categoryId':  '22'
        },
        'status': {
            'privacyStatus':           'public',
            'selfDeclaredMadeForKids': False
        }
    }
    file_size = os.path.getsize(video_path)
    init_res = requests.post(
        'https://www.googleapis.com/upload/youtube/v3/videos'
        '?uploadType=resumable&part=snippet,status',
        headers={
            'Authorization':           f'Bearer {access_token}',
            'Content-Type':            'application/json',
            'X-Upload-Content-Type':   'video/mp4',
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
            'apikey':        SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type':  'application/json'
        },
        json={
            'published':        True,
            'published_at':     datetime.now(timezone.utc).isoformat(),
            'youtube_video_id': youtube_video_id
        }
    )


def post_pinned_comment(yt_video_id, comment_text):
    try:
        access_token = get_youtube_access_token()
        insert_res = requests.post(
            'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type':  'application/json'
            },
            json={
                'snippet': {
                    'videoId': yt_video_id,
                    'topLevelComment': {
                        'snippet': {'textOriginal': comment_text}
                    }
                }
            },
            timeout=30
        )
        insert_res.raise_for_status()
        comment_id = insert_res.json()['snippet']['topLevelComment']['id']
        print(f'[Publish] Comment posted: {comment_id}')
        pin_res = requests.post(
            'https://www.googleapis.com/youtube/v3/comments?part=snippet',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type':  'application/json'
            },
            json={
                'id': comment_id,
                'snippet': {
                    'moderationStatus': 'heldForReview',
                    'isPinned': True
                }
            },
            timeout=30
        )
        print(f'[Publish] Comment pinned. Status: {pin_res.status_code}')
    except Exception as e:
        print(f'[Publish] Pinned comment failed (non-fatal): {e}')


def publish_to_youtube_job(script_id):
    video_path = None
    try:
        print(f'[Publish] Starting YouTube publish for script {script_id}')
        video_record = get_video_record(script_id)
        video_url    = video_record.get('video_url')
        if not video_url:
            print(f'[Publish] No video_url found for script {script_id}')
            return
        script = get_script(script_id)
        setup  = script.get('setup', 'Mr. Oldverdict')
        lines  = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)
        title = setup[:93] + ' #Shorts'
        line1 = strip_emotion_tags(lines[0]['text']) if lines else ''
        line2 = lines[1]['text'] if len(lines) > 1 else ''
        theme_tags = script.get('theme_tags', [])
        if isinstance(theme_tags, str):
            theme_tags = json.loads(theme_tags)
        topic_hashtags = ' '.join(f'#{t.replace(" ", "")}' for t in theme_tags if t)
        base_hashtags  = '#mroldverdict #Shorts #comedy #wisdom #observations'
        all_hashtags   = f'{base_hashtags} {topic_hashtags}'.strip()
        description    = f'{line1}\n\n{line2}\n\n{all_hashtags}'
        tags = (
            ['mroldverdict', 'shorts', 'comedy', 'wisdom', 'observations', 'oldverdict']
            + [t.replace(' ', '') for t in theme_tags if t]
        )
        video_path = download_file(video_url, '.mp4')
        yt_id = upload_to_youtube(video_path, title, description, tags)
        print(f'[Publish] YouTube video ID: {yt_id}')
        mark_script_published(script_id, yt_id)
        pinned_comment = script.get('pinned_comment')
        if pinned_comment and isinstance(pinned_comment, str) and pinned_comment.strip():
            post_pinned_comment(yt_id, pinned_comment.strip())
        print(f'[Publish] Done. https://youtube.com/shorts/{yt_id}')
    except Exception as e:
        import traceback
        print(f'[Publish] Error: {e}')
        print(traceback.format_exc())
    finally:
        if video_path and os.path.exists(video_path):
            _try_unlink(video_path)

# ── Instagram helpers ──────────────────────────────────────────────────────────

def build_instagram_caption(script_row):
    lines = script_row.get('lines', [])
    if isinstance(lines, str):
        lines = json.loads(lines)
    if len(lines) >= 2:
        raw = lines[1].get('text', '')
    else:
        raw = script_row.get('setup', '')
    clean = re.sub(r'^\[[^\]]+\]\s*', '', raw).strip()
    theme_tags = script_row.get('theme_tags', [])
    if isinstance(theme_tags, str):
        theme_tags = json.loads(theme_tags)
    topic_hashtags = ' '.join(f'#{t.replace(" ", "")}' for t in theme_tags if t)
    all_hashtags   = f'{INSTAGRAM_HASHTAGS} {topic_hashtags}'.strip()
    return f'{clean}\n\n{all_hashtags}'


def publish_reel_to_instagram(video_public_url, caption):
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        raise ValueError('IG_ACCESS_TOKEN or IG_ACCOUNT_ID not set in environment')
    base = f'https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}'
    container_resp = requests.post(
        f'{base}/media',
        data={
            'media_type':    'REELS',
            'video_url':     video_public_url,
            'caption':       caption,
            'share_to_feed': 'true',
            'access_token':  IG_ACCESS_TOKEN,
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
        status_code = status_resp.json().get('status_code', '')
        print(f'[Instagram] Container status ({attempt + 1}/30): {status_code}')
        if status_code == 'FINISHED':
            break
        if status_code == 'ERROR':
            raise RuntimeError(f'Container processing error: {status_resp.json()}')
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
            'apikey':        SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type':  'application/json'
        },
        json={'instagram_media_id': instagram_media_id}
    )


def publish_to_instagram_job(script_id):
    video_path = None
    try:
        print(f'[Instagram] Starting publish for script {script_id}')
        video_record = get_video_record(script_id)
        video_url    = video_record.get('video_url')
        if not video_url:
            print(f'[Instagram] No video_url for script {script_id}')
            return None
        script  = get_script(script_id)
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
            _try_unlink(video_path)

# ── Caption rendering ──────────────────────────────────────────────────────────

def _load_bold_font(size):
    """Load DejaVu Serif Bold at given size. Returns (font, path)."""
    paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size), p
            except Exception:
                continue
    return ImageFont.load_default(), None


def _find_serif_font():
    """Return path to a serif font for ffmpeg drawtext."""
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def render_caption_for_bar(text, width=VIDEO_W, bar_h=BAR_H):
    """
    Render caption text as RGBA PNG sized to fit the letterbox bar.
    Transparent background — overlaid on top of the black drawbox bar.
    White text with black stroke, vertically centered in bar.
    Returns numpy RGBA array (width x bar_h).
    """
    font_size = 36
    padding_x = 28
    font, font_path = _load_bold_font(font_size)

    img  = PIL.Image.new('RGBA', (width, bar_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Shrink font until text fits width
    while font_size >= 20:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw   = bbox[2] - bbox[0]
        if tw <= width - padding_x * 2:
            break
        font_size -= 2
        font, font_path = _load_bold_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (width - tw) // 2
    y = (bar_h - th) // 2 - 2

    # Black stroke (2px)
    stroke = 2
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))

    # White fill
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return np.array(img)


def build_caption_timing(setup_text, lines, voice_dur):
    """
    Compute start/end times for each caption segment.
    Returns list of {'text': str, 'start': float, 'end': float}
    """
    all_items = []
    if setup_text:
        all_items.append({'text': setup_text, 'pause_after': True})
    for line in lines:
        all_items.append(line)

    if not all_items:
        return []

    cleaned = [strip_emotion_tags(item.get('text', '')) for item in all_items]
    weights = []
    for i, item in enumerate(all_items):
        w = max(len(cleaned[i]), 1)
        if item.get('pause_after', False):
            w = int(w * 1.65)
        weights.append(w)
    total_weight = sum(weights)

    segments  = []
    current_t = 0.0
    for i, text in enumerate(cleaned):
        if not text:
            current_t += (weights[i] / total_weight) * voice_dur
            continue
        seg_dur = (weights[i] / total_weight) * voice_dur
        seg_dur = min(seg_dur, voice_dur - current_t)
        if seg_dur <= 0:
            break
        segments.append({
            'text':  text,
            'start': current_t,
            'end':   current_t + seg_dur,
        })
        current_t += seg_dur

    return segments

# ── ffmpeg helpers ─────────────────────────────────────────────────────────────

def get_audio_duration(audio_path):
    result = subprocess.run(
        [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ],
        capture_output=True, text=True, timeout=30
    )
    return float(result.stdout.strip())


def run_ffmpeg(cmd, label='ffmpeg'):
    """Run ffmpeg. Always log stderr. Raise on failure."""
    print(f'[{label}] Running...')
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=360)
    if result.returncode != 0:
        print(f'[{label}] STDERR:\n{result.stderr}')
        raise RuntimeError(
            f'{label} failed (rc={result.returncode}): {result.stderr[-600:]}'
        )
    print(f'[{label}] Done.')


def _try_unlink(path):
    if path and os.path.exists(path):
        try:
            os.unlink(path)
        except Exception:
            pass

# ── Video assembly ─────────────────────────────────────────────────────────────

def assemble_video(image_path, audio_path, lines, output_path,
                   setup_text=None, expression='flat_observation'):
    """
    Assemble Mr. Oldverdict video using two ffmpeg passes.

    Visual structure:
    - Expression-driven color grade (eq + hue), film grain (noise), pan motion
    - Cinematic letterbox bars (top + bottom, 90px each) during voice only
    - Captions as PIL-rendered PNGs overlaid on the bottom bar
    - @mroldverdict watermark (bottom right, 45% opacity)
    - Post-voice clean hold (2.2s) then fade to black (0.6s)
    - 1s black hold appended at end (no outro card)

    Pass 1: looped image + all effects + captions → temp_main.mp4
    Pass 2: concat temp_main.mp4 + 1s black → output_path
    """
    preset = get_expression_preset(expression)
    print(f'[assemble] expression={expression} preset={preset}')

    # ── Timings ──────────────────────────────────────────────────────────────
    voice_dur    = get_audio_duration(audio_path)
    post_hold    = 2.2
    fade_dur     = 0.6
    main_dur     = voice_dur + post_hold
    total_dur    = main_dur + fade_dur
    total_frames = int(total_dur * FPS)

    print(f'[assemble] voice={voice_dur:.2f}s  total={total_dur:.2f}s  frames={total_frames}')

    # ── Image scale and pan math ──────────────────────────────────────────────
    pil_img = PIL.Image.open(image_path)
    img_w, img_h = pil_img.size
    pil_img.close()

    fill_scale = max(VIDEO_W / img_w, VIDEO_H / img_h)
    pan_scale  = fill_scale * 1.15      # 15% extra room for pan motion
    scaled_w   = int(img_w * pan_scale)
    scaled_h   = int(img_h * pan_scale)
    x_center   = max(0, (scaled_w - VIDEO_W) // 2)
    y_center   = max(0, (scaled_h - VIDEO_H) // 2)
    x_max      = max(0, scaled_w - VIDEO_W)

    pan_dir   = preset['pan']
    pan_range = 20   # pixels of travel over full clip

    if pan_dir == 'left':
        x_start = min(x_center + pan_range // 2, x_max)
        x_expr  = f"clip({x_start}-{pan_range}*n/{total_frames},0,{x_max})"
    elif pan_dir == 'right':
        x_start = max(x_center - pan_range // 2, 0)
        x_expr  = f"clip({x_start}+{pan_range}*n/{total_frames},0,{x_max})"
    else:
        x_expr = str(x_center)

    print(f'[assemble] img={img_w}x{img_h}  scaled={scaled_w}x{scaled_h}  '
          f'x_center={x_center}  pan={pan_dir}')

    # ── Caption PNGs ──────────────────────────────────────────────────────────
    caption_segments  = build_caption_timing(setup_text, lines, voice_dur)
    caption_png_paths = []

    for seg in caption_segments:
        arr      = render_caption_for_bar(seg['text'])
        png_path = tempfile.mktemp(suffix='.png')
        PIL.Image.fromarray(arr).save(png_path)
        caption_png_paths.append(png_path)
        print(f'[caption] "{seg["text"][:45]}"  '
              f'{seg["start"]:.2f}s → {seg["end"]:.2f}s')

    # ── Build filter_complex ──────────────────────────────────────────────────
    eq_str  = preset['eq']
    hue_str = preset['hue']
    grain   = preset['grain']

    wm_font    = _find_serif_font()
    wm_font_kv = f':fontfile={wm_font}' if wm_font else ''
    voice_end  = f'{voice_dur:.3f}'

    fc = []

    # Step 1: scale → setsar → crop with pan → color grade → film grain
    fc.append(
        f"[0:v]setpts=PTS,"
        f"scale={scaled_w}:{scaled_h}:flags=lanczos,"
        f"setsar=1,"
        f"crop={VIDEO_W}:{VIDEO_H}:{x_expr}:{y_center},"
        f"eq={eq_str},"
        f"hue={hue_str},"
        f"noise=c0s={grain}:c0f=t+u"
        f"[grained]"
    )

    # Step 2: letterbox bars — top and bottom, active only during voice
    fc.append(
        f"[grained]"
        f"drawbox=x=0:y=0:w={VIDEO_W}:h={BAR_H}:"
        f"color=black:t=fill:enable='lte(t,{voice_end})'"
        f"[bb1]"
    )
    fc.append(
        f"[bb1]"
        f"drawbox=x=0:y={BOT_BAR_Y}:w={VIDEO_W}:h={BAR_H}:"
        f"color=black:t=fill:enable='lte(t,{voice_end})'"
        f"[bb2]"
    )

    # Step 3: caption PNG overlays (inputs 1..N, each active in its window)
    current_label = 'bb2'
    for i, seg in enumerate(caption_segments):
        in_idx    = i + 1       # input 0 = image, 1..N = caption PNGs
        out_label = f'ov{i}'
        fc.append(
            f"[{current_label}][{in_idx}:v]"
            f"overlay=0:{BOT_BAR_Y}:"
            f"enable='between(t,{seg['start']:.3f},{seg['end']:.3f})'"
            f"[{out_label}]"
        )
        current_label = out_label

    # Step 4: @mroldverdict watermark — just above the bottom bar, bottom right
    wm_y = BOT_BAR_Y - 28
    fc.append(
        f"[{current_label}]"
        f"drawtext="
        f"text='@mroldverdict'"
        f"{wm_font_kv}"
        f":fontsize=22"
        f":fontcolor=white@0.45"
        f":x=w-tw-18"
        f":y={wm_y}"
        f":borderw=2"
        f":bordercolor=black@0.45"
        f"[watermarked]"
    )

    # Step 5: fade to black at end of main_dur
    fc.append(
        f"[watermarked]fade=t=out:st={main_dur:.3f}:d={fade_dur:.3f}[vout]"
    )

    # Step 6: audio — fadein + fadeout + pad silence to video length
    audio_idx        = len(caption_segments) + 1
    audio_fadeout_st = max(0.0, voice_dur - 0.5)
    fc.append(
        f"[{audio_idx}:a]"
        f"afade=t=in:st=0:d=0.3,"
        f"afade=t=out:st={audio_fadeout_st:.3f}:d=0.5,"
        f"apad"
        f"[aout]"
    )

    fc_str = ';'.join(fc)

    # ── Pass 1: render main clip ──────────────────────────────────────────────
    temp_main = tempfile.mktemp(suffix='_main.mp4')
    cmd1 = ['ffmpeg', '-y']
    cmd1 += ['-loop', '1', '-framerate', str(FPS), '-i', image_path]
    for png in caption_png_paths:
        cmd1 += ['-i', png]
    cmd1 += ['-i', audio_path]
    cmd1 += [
        '-filter_complex', fc_str,
        '-map',    '[vout]',
        '-map',    '[aout]',
        '-t',      str(total_dur),
        '-r',      str(FPS),
        '-vcodec', 'libx264',
        '-crf',    '28',
        '-preset', 'ultrafast',
        '-acodec', 'aac',
        temp_main
    ]

    try:
        run_ffmpeg(cmd1, label='pass1-main')
    except Exception:
        _try_unlink(temp_main)
        for p in caption_png_paths:
            _try_unlink(p)
        raise

    # ── Pass 2: append 1s black hold ─────────────────────────────────────────
    cmd2 = [
        'ffmpeg', '-y',
        '-i', temp_main,
        '-f', 'lavfi', '-t', '1.0',
        '-i', f'color=c=black:s={VIDEO_W}x{VIDEO_H}:r={FPS}',
        '-f', 'lavfi', '-t', '1.0',
        '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-filter_complex',
        (
            '[0:v][1:v]concat=n=2:v=1:a=0[vout];'
            '[0:a][2:a]concat=n=2:v=0:a=1[aout]'
        ),
        '-map',    '[vout]',
        '-map',    '[aout]',
        '-vcodec', 'libx264',
        '-crf',    '28',
        '-preset', 'ultrafast',
        '-acodec', 'aac',
        output_path
    ]

    try:
        run_ffmpeg(cmd2, label='pass2-black')
    finally:
        _try_unlink(temp_main)
        for p in caption_png_paths:
            _try_unlink(p)

    print(f'[assemble] Complete → {output_path}')

# ── Pipeline orchestration ─────────────────────────────────────────────────────

def run_pipeline_job():
    print('[Pipeline] Starting automated pipeline run...')
    image_path = audio_path = output_path = None

    try:
        print('[Pipeline] Step 1: Calling council worker...')
        council_res = requests.post(
            COUNCIL_URL,
            headers={
                'Authorization': f'Bearer {BEARER}',
                'Content-Type':  'application/json'
            },
            json={},
            timeout=60
        )
        council_res.raise_for_status()
        council_data = council_res.json()
        script_id    = council_data.get('script_id')

        if not script_id:
            print(f'[Pipeline] Council failed: {council_data}')
            return

        print(f'[Pipeline] Script generated: {script_id}')

        print('[Pipeline] Step 2: Calling voice and image workers simultaneously...')

        def call_voice():
            res = requests.post(
                VOICE_URL,
                headers={'Authorization': f'Bearer {BEARER}', 'Content-Type': 'application/json'},
                json={'script_id': script_id},
                timeout=120
            )
            return ('voice', res.status_code, res.text)

        def call_image():
            res = requests.post(
                IMAGE_URL,
                headers={'Authorization': f'Bearer {BEARER}', 'Content-Type': 'application/json'},
                json={'script_id': script_id},
                timeout=120
            )
            return ('image', res.status_code, res.text)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(call_voice), executor.submit(call_image)]
            for future in as_completed(futures):
                label, status, body = future.result()
                print(f'[Pipeline] {label} worker: {status} - {body[:200]}')

        print('[Pipeline] Step 3: Polling for voice and image...')
        max_wait = 300; poll_interval = 10; elapsed = 0
        voice_ready = image_ready = False

        while elapsed < max_wait:
            try:
                rec         = get_video_record(script_id)
                voice_ready = bool(rec.get('voice_file_url'))
                image_ready = bool(rec.get('image_url'))
                print(f'[Pipeline] Poll {elapsed}s — voice:{voice_ready} image:{image_ready}')
                if voice_ready and image_ready:
                    break
            except Exception as e:
                print(f'[Pipeline] Poll error: {e}')
            time.sleep(poll_interval)
            elapsed += poll_interval

        if not voice_ready or not image_ready:
            print(f'[Pipeline] Timeout. voice:{voice_ready} image:{image_ready}')
            return

        print('[Pipeline] Step 4: Assembling video...')
        video_record = get_video_record(script_id)
        script       = get_script(script_id)

        image_path  = download_file(video_record['image_url'], '.jpg')
        audio_path  = download_file(video_record['voice_file_url'], '.mp3')
        output_path = tempfile.mktemp(suffix='.mp4')

        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)

        assemble_video(
            image_path, audio_path, lines, output_path,
            setup_text=script.get('setup'),
            expression=script.get('expression', 'flat_observation')
        )

        video_url = upload_video(script_id, output_path)
        update_video_record(script_id, video_url)
        print(f'[Pipeline] Done. Video: {video_url}')

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
        for path in [image_path, audio_path, output_path]:
            _try_unlink(path)


def assemble_job(script_id, auto_publish=False):
    image_path = audio_path = output_path = None
    try:
        video_record = get_video_record(script_id)
        script       = get_script(script_id)

        image_url = video_record.get('image_url')
        audio_url = video_record.get('voice_file_url')

        if not image_url:
            print(f'[assemble_job] No image for {script_id}'); return
        if not audio_url:
            print(f'[assemble_job] No audio for {script_id}'); return

        image_path  = download_file(image_url, '.jpg')
        audio_path  = download_file(audio_url, '.mp3')
        output_path = tempfile.mktemp(suffix='.mp4')

        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)

        assemble_video(
            image_path, audio_path, lines, output_path,
            setup_text=script.get('setup'),
            expression=script.get('expression', 'flat_observation')
        )

        video_url = upload_video(script_id, output_path)
        update_video_record(script_id, video_url)
        print(f'[assemble_job] Done: {video_url}')

        if auto_publish:
            publish_to_youtube_job(script_id)
            publish_to_instagram_job(script_id)

    except Exception as e:
        import traceback
        print(f'[assemble_job] Error: {e}')
        print(traceback.format_exc())
    finally:
        for path in [image_path, audio_path, output_path]:
            _try_unlink(path)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status':  'Mr. Oldverdict assembly standing by.',
        'version': 'modal-v1'
    })


@app.route('/run-pipeline', methods=['POST'])
def run_pipeline():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    thread = threading.Thread(target=run_pipeline_job, daemon=True)
    thread.start()
    return jsonify({
        'status':  'Pipeline started',
        'message': 'Council → Voice + Image → Assembly → YouTube → Instagram'
    }), 202


@app.route('/assemble', methods=['POST'])
def assemble():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data      = request.get_json()
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400
    thread = threading.Thread(target=assemble_job, args=(script_id, False), daemon=True)
    thread.start()
    return jsonify({
        'status':    'Assembly started',
        'script_id': script_id,
        'message':   'Poll /video-status. Use /publish when ready.'
    }), 202


@app.route('/video-status', methods=['GET'])
def video_status():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    script_id = request.args.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id required'}), 400
    try:
        res = requests.get(
            f'{SUPABASE_URL}/rest/v1/videos'
            f'?script_id=eq.{script_id}'
            f'&select=video_url,voice_file_url,image_url',
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
        )
        rows = res.json()
        if rows and rows[0].get('video_url'):
            return jsonify({'ready': True, 'video_url': rows[0]['video_url']})
        return jsonify({'ready': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/publish', methods=['POST'])
def publish():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data      = request.get_json()
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400
    publish_to_youtube_job(script_id)
    return jsonify({'status': 'Publish complete', 'script_id': script_id}), 200


@app.route('/publish-instagram', methods=['POST'])
def publish_instagram():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data      = request.get_json() or {}
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        return jsonify({'error': 'IG_ACCESS_TOKEN or IG_ACCOUNT_ID not set'}), 500
    media_id = publish_to_instagram_job(script_id)
    if media_id:
        return jsonify({'success': True, 'media_id': media_id, 'script_id': script_id}), 200
    return jsonify({
        'success': False, 'error': 'Instagram publish failed', 'script_id': script_id
    }), 500


@app.route('/videos/list', methods=['GET', 'OPTIONS'])
def videos_list():
    if request.method == 'OPTIONS':
        return '', 204, {
            'Access-Control-Allow-Origin':  '*',
            'Access-Control-Allow-Headers': 'Authorization,Content-Type',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        }
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        res = requests.get(
            f'{SUPABASE_URL}/rest/v1/videos'
            f'?select=id,script_id,video_url,created_at,scripts(setup,published,category)'
            f'&video_url=not.is.null'
            f'&order=created_at.desc',
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
        )
        return jsonify({'videos': res.json()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/videos/delete', methods=['POST', 'OPTIONS'])
def videos_delete():
    if request.method == 'OPTIONS':
        return '', 204, {
            'Access-Control-Allow-Origin':  '*',
            'Access-Control-Allow-Headers': 'Authorization,Content-Type',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        }
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data      = request.get_json() or {}
    script_id = data.get('script_id')
    if not script_id:
        return jsonify({'error': 'script_id required'}), 400
    try:
        requests.delete(
            f'{SUPABASE_URL}/storage/v1/object/revdlo-media/videos/{script_id}.mp4',
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
        )
        requests.delete(
            f'{SUPABASE_URL}/rest/v1/videos?script_id=eq.{script_id}',
            headers={
                'apikey':        SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Prefer':        'return=minimal'
            }
        )
        return jsonify({'deleted': True, 'script_id': script_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/videos/incomplete', methods=['GET'])
def videos_incomplete():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        res = requests.get(
            f'{SUPABASE_URL}/rest/v1/videos'
            f'?select=id,script_id,voice_file_url,image_url,video_url,created_at,'
            f'scripts(setup,category,raw_topic)'
            f'&voice_file_url=not.is.null'
            f'&image_url=not.is.null'
            f'&video_url=is.null'
            f'&order=created_at.desc',
            headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
        )
        return jsonify({'incomplete': res.json()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Modal entry point ──────────────────────────────────────────────────────────

@modal_app.function(
    image=modal_image,
    secrets=secrets,
    cpu=2.0,
    memory=2048,
    timeout=600
)
@modal.wsgi_app()
def web():
    return app


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)