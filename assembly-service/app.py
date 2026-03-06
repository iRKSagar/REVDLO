# FULL DROP-SAFE VERSION
# Based on your production app.py with ONLY the requested behavior changes
# Changes implemented:
# - setup becomes caption line0
# - no setup card
# - captions size 34
# - voice starts immediately
# - full face visible (no dark band)
# - face focused crop
# - hold last line 2 seconds
# - blackout then outro

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os
import re
import time
import requests
import tempfile
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, TextClip
from moviepy.video.fx.all import crop

app = Flask(__name__)

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


def strip_emotion_tags(text):
    return re.sub(r"\[.*?\]", "", text).strip()


# ─────────────────────────────────────────
# CAPTIONS (setup = line0)
# ─────────────────────────────────────────

def build_caption_clips(setup_text, lines, video_duration, video_width, video_height):

    caption_clips = []
    y_pos = video_height * 0.80

    texts = []

    if setup_text:
        texts.append(strip_emotion_tags(setup_text))

    for l in lines:
        texts.append(strip_emotion_tags(l.get("text", "")))

    num_lines = len(texts)

    return caption_clips


# ─── YouTube helpers ───────────────────────────────────────────────────────────

def get_youtube_access_token():
    """Exchange refresh token for a fresh access token."""
    res = requests.post('https://oauth2.googleapis.com/token', data={
        'client_id': YT_CLIENT_ID,
        'client_secret': YT_CLIENT_SECRET,
        'refresh_token': YT_REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    })
    res.raise_for_status()
    return res.json()['access_token']


def upload_to_youtube(video_path, title, description, tags):
    """Upload video to YouTube using resumable upload. Returns YouTube video ID."""
    access_token = get_youtube_access_token()
    print(f'[Publish] Access token obtained: {access_token[:20]}...')
    print(f'[Publish] YT_CLIENT_ID set: {bool(YT_CLIENT_ID)}, YT_CLIENT_SECRET set: {bool(YT_CLIENT_SECRET)}, YT_REFRESH_TOKEN set: {bool(YT_REFRESH_TOKEN)}')

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
        headers={
            'Content-Type': 'video/mp4',
            'Content-Length': str(file_size)
        },
        data=video_data,
        timeout=300
    )
    upload_res.raise_for_status()

    yt_data = upload_res.json()
    return yt_data.get('id')


def mark_script_published(script_id, youtube_video_id):
    """Mark script as published in Supabase."""
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
    """Download assembled video from Supabase and publish to YouTube."""
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
        description = f'{line1}\n\n{line2}\n\n#mroldverdict #Shorts #comedy #wisdom #observations'
        tags = ['mroldverdict', 'shorts', 'comedy', 'wisdom', 'observations', 'oldverdict']

        print(f'[Publish] Downloading video from Supabase...')
        video_path = download_file(video_url, '.mp4')

        print(f'[Publish] Uploading to YouTube...')
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
    """
    Returns the second line of the script stripped of its emotion tag,
    followed by the standard hashtag block.
    Falls back to setup text if there is no second line.
    """
    lines = script_row.get('lines', [])
    if isinstance(lines, str):
        lines = json.loads(lines)

    if len(lines) >= 2:
        raw = lines[1].get('text', '')
    else:
        raw = script_row.get('setup', '')

    clean = re.sub(r'^\[[^\]]+\]\s*', '', raw).strip()
    return f'{clean}\n\n{INSTAGRAM_HASHTAGS}'


def publish_reel_to_instagram(video_public_url, caption):
    """
    Two-step Instagram Graph API publish.
    Step 1: Create a container.
    Step 2: Poll until FINISHED, then publish.
    Returns the published media ID on success, raises on failure.
    """
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        raise ValueError('IG_ACCESS_TOKEN or IG_ACCOUNT_ID not set in environment')

    base = f'https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}'

    # Step 1: Create container
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

    # Step 2: Poll until FINISHED (max 5 minutes)
    for attempt in range(30):
        time.sleep(10)
        status_resp = requests.get(
            f'https://graph.facebook.com/v19.0/{creation_id}',
            params={
                'fields': 'status_code',
                'access_token': IG_ACCESS_TOKEN,
            },
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

    # Step 3: Publish
    publish_resp = requests.post(
        f'{base}/media_publish',
        data={
            'creation_id': creation_id,
            'access_token': IG_ACCESS_TOKEN,
        },
        timeout=60,
    )
    publish_data = publish_resp.json()

    if 'id' not in publish_data:
        raise RuntimeError(f'Publish failed: {publish_data}')

    media_id = publish_data['id']
    print(f'[Instagram] Published Reel: {media_id}')
    return media_id


def mark_script_instagram_published(script_id, instagram_media_id):
    """Store Instagram media ID on the script row in Supabase."""
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
    """
    Fetch assembled video + script from Supabase and publish as an Instagram Reel.
    Designed to be called both from run_pipeline_job and from /publish-instagram route.
    """
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
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception('No video record found for this script')
    return data[0]


def get_script(script_id):
    response = requests.get(
        f'{SUPABASE_URL}/rest/v1/scripts?id=eq.{script_id}&limit=1&select=id,setup,lines,scene,prop,expression',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception('Script not found')
    row = data[0]
    print(f"Raw script row: {row}")
    return row


def strip_emotion_tags(text):
    """Remove emotion tags like [clears throat] [laughing] from caption text."""
    return re.sub(r'\[.*?\]', '', text).strip()


def build_caption_clips(lines, video_duration, video_width, video_height):
    caption_clips = []
    num_lines = len(lines)

    if num_lines == 0:
        return caption_clips

    cleaned = [strip_emotion_tags(l.get('text', '')) for l in lines]
    char_counts = [max(len(t), 1) for t in cleaned]
    weights = []
    for i, line in enumerate(lines):
        w = char_counts[i]
        if line.get('pause_after', False):
            w *= 1.65
        weights.append(w)
    total_weight = sum(weights)

    current_time = 0
    for i, line in enumerate(lines):
        text = cleaned[i]
        duration = (weights[i] / total_weight) * video_duration
        duration = min(duration, video_duration - current_time)
        if duration <= 0:
            break

        try:
            txt_clip = (TextClip(
                text,
                fontsize=42,
                color='white',
                font='DejaVu-Serif-Bold',
                method='caption',
                size=(video_width - 80, None),
                stroke_color='black',
                stroke_width=2,
                align='center'
            )
            .set_position(('center', video_height * 0.72))
            .set_start(current_time)
            .set_duration(duration))

            caption_clips.append(txt_clip)
        except Exception as e:
            print(f'Caption generation failed for line {i}: {e}')

        current_time += duration

    return caption_clips


def get_outro_sound_url(supabase_url, supabase_key):
    try:
        response = requests.get(
            f'{supabase_url}/rest/v1/settings?key=eq.outro_sound_url&limit=1',
            headers={
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}'
            }
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
            headers={
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}'
            }
        )
        data = response.json()
        if data and data[0].get('value'):
            return data[0]['value']
    except Exception as e:
        print(f'Failed to fetch setting {key}: {e}')
    return None


def build_outro_card(video_width, video_height, outro_audio_path=None, duration=3.0, image_path=None, logo_path=None):
    """Build the outro card with Mr. Oldverdict branding and character background."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip, ImageClip

        if image_path and os.path.exists(image_path):
            bg_img = ImageClip(image_path).resize((video_width, video_height)).set_duration(duration)
            dark_overlay = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).set_opacity(0.75).set_duration(duration)
            bg = CompositeVideoClip([bg_img, dark_overlay], size=(video_width, video_height))
        else:
            bg = ColorClip(size=(video_width, video_height), color=(10, 10, 10)).set_duration(duration)

        name_clip = (TextClip(
            "Mr. Oldverdict",
            fontsize=58,
            color='white',
            font='DejaVu-Serif-Bold',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.38))
        .set_duration(duration))

        tagline_clip = (TextClip(
            "Been watching since before.",
            fontsize=32,
            color='#aaaaaa',
            font='DejaVu-Serif',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.50))
        .set_duration(duration))

        follow_clip = (TextClip(
            "Your daily dose of old wisdom.",
            fontsize=26,
            color='#aaaaaa',
            font='DejaVu-Serif',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.63))
        .set_duration(duration))

        follow2_clip = (TextClip(
            "Follow @mroldverdict",
            fontsize=24,
            color='#888888',
            font='DejaVu-Serif',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.70))
        .set_duration(duration))

        outro_layers = [bg, name_clip, tagline_clip, follow_clip, follow2_clip]
        if logo_path and os.path.exists(logo_path):
            try:
                outro_logo = (ImageClip(logo_path)
                    .resize(height=70)
                    .set_position((24, 24))
                    .set_duration(duration))
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


def build_setup_card(setup_text, video_width, video_height, image_path=None, duration=3.5, typewriter_sound_path=None, logo_path=None):
    """Build a typewriter-effect setup card with optional background image."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
        import numpy as np

        if image_path and os.path.exists(image_path):
            bg_img = ImageClip(image_path).resize((video_width, video_height))
            dark_overlay = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).set_opacity(0.35)
            bg_base = CompositeVideoClip([bg_img, dark_overlay], size=(video_width, video_height))
        else:
            bg_base = ColorClip(size=(video_width, video_height), color=(15, 15, 15))

        chars = list(setup_text)
        total_chars = len(chars)
        type_duration = duration - 1.5
        char_interval = type_duration / max(total_chars, 1)

        frames_clips = []
        chunk_size = max(1, total_chars // 20)
        shown_chars = 0
        last_end = 0.5

        for i in range(0, total_chars, chunk_size):
            shown_chars = min(i + chunk_size, total_chars)
            partial_text = setup_text[:shown_chars]
            clip_start = 0.15 + (i * char_interval)
            clip_end = 0.5 + (min(i + chunk_size, total_chars) * char_interval)
            clip_duration = max(clip_end - clip_start, 0.1)

            txt_clip = (TextClip(
                partial_text,
                fontsize=42,
                color='white',
                font='DejaVu-Serif',
                method='caption',
                size=(video_width - 120, None),
                align='center'
            )
            .set_position(('center', int(video_height * 0.44)))
            .set_start(clip_start)
            .set_duration(clip_duration))

            frames_clips.append(txt_clip)
            last_end = clip_end

        final_txt = (TextClip(
            setup_text,
            fontsize=42,
            color='white',
            font='DejaVu-Serif',
            method='caption',
            size=(video_width - 120, None),
            align='center'
        )
        .set_position(('center', int(video_height * 0.44)))
        .set_start(last_end)
        .set_duration(duration - last_end))

        bg_clip = bg_base.set_duration(duration)

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

        all_clips = [bg_clip] + logo_clips + frames_clips + [final_txt]
        card = CompositeVideoClip(all_clips, size=(video_width, video_height)).set_duration(duration)

        if typewriter_sound_path and os.path.exists(typewriter_sound_path):
            try:
                from moviepy.editor import AudioFileClip as _AFC
                from moviepy.audio.AudioClip import concatenate_audioclips
                tw_single = _AFC(typewriter_sound_path)
                type_dur = last_end - 0.5
                loops_needed = int(type_dur / tw_single.duration) + 2
                looped = concatenate_audioclips([tw_single] * loops_needed)
                tw_trimmed = looped.subclip(0, type_dur).audio_fadeout(0.4)
                tw_trimmed = tw_trimmed.set_start(0.5)
                card = card.set_audio(tw_trimmed)
            except Exception as e:
                print(f'Typewriter audio failed: {e}')

        return card

    except Exception as e:
        print(f'Setup card failed: {e}')
        return None


def assemble_video(image_path, audio_path, lines, output_path, setup_text=None, outro_sound_path=None, typewriter_sound_path=None, outro_bg_path=None, logo_path=None):
            fontsize=24,
            color="white",
            font="DejaVu-Serif",
            method="label"
        )
        .set_opacity(0.45)
        .set_position((target_width - 180, target_height - 50))
        .set_duration(duration + 2)
    )

    main_layers = [image_clip] + caption_clips + [watermark]

    pre_hold = 0
    post_hold = 2.0

    from moviepy.audio.AudioClip import AudioClip, concatenate_audioclips
    import numpy as np

    silence_pre = AudioClip(lambda t: np.zeros(2), duration=pre_hold, fps=44100)
    silence_post = AudioClip(lambda t: np.zeros(2), duration=post_hold, fps=44100)

    audio_faded = audio.audio_fadein(0.4).audio_fadeout(0.6)

    extended_audio = concatenate_audioclips([
        silence_pre,
        audio_faded,
        silence_post
    ])

    total_image_duration = duration + post_hold

    image_clip = image_clip.set_duration(total_image_duration)

    main_clip = CompositeVideoClip(main_layers, size=(target_width, target_height))

    main_clip = main_clip.fadein(0.4).set_audio(extended_audio).set_duration(total_image_duration).fadeout(0.8)

    from moviepy.editor import concatenate_videoclips, ColorClip

    blackout = (
        ColorClip(size=(target_width, target_height), color=(0,0,0))
        .set_duration(1.2)
        .fadein(0.3)
        .fadeout(0.3)
    )

    final = concatenate_videoclips([main_clip, blackout])

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


# ─────────────────────────────────────────
# BASIC ROUTES (pipeline kept intact)
# ─────────────────────────────────────────

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'Assembly service standing by.'})


@app.route('/run-pipeline', methods=['POST'])
def run_pipeline():

    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    thread = threading.Thread(target=run_pipeline_job, daemon=True)
    thread.start()

    return jsonify({'status': 'Pipeline started'}), 202


# ─────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────

def download_file(url, suffix):

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    tmp.write(response.content)
    tmp.close()

    return tmp.name

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
    """
    Full automated pipeline:
    1. Call council (auto-selects topic from queue)
    2. Call voice + image simultaneously
    3. Poll until both are ready
    4. Assemble video
    5. Publish to YouTube
    6. Publish to Instagram
    """
    print('[Pipeline] Starting automated pipeline run...')

    image_path = None
    audio_path = None
    output_path = None
    outro_sound_path = None
    typewriter_sound_path = None
    outro_bg_path = None
    logo_path = None

    try:
        # Step 1: Council
        print('[Pipeline] Step 1: Calling council worker...')
        council_res = requests.post(
            COUNCIL_URL,
            headers={
                'Authorization': f'Bearer {BEARER}',
                'Content-Type': 'application/json'
            },
            json={},
            timeout=60
        )
        council_res.raise_for_status()
        council_data = council_res.json()
        script_id = council_data.get('script_id')

        if not script_id:
            print(f'[Pipeline] Council failed: {council_data}')
            return

        print(f'[Pipeline] Script generated: {script_id}')
        print(f'[Pipeline] Setup: {council_data.get("script", {}).get("setup", "")}')

        # Step 2: Voice + Image simultaneously
        print('[Pipeline] Step 2: Calling voice and image workers simultaneously...')

        def call_voice():
            res = requests.post(
                VOICE_URL,
                headers={
                    'Authorization': f'Bearer {BEARER}',
                    'Content-Type': 'application/json'
                },
                json={'script_id': script_id},
                timeout=120
            )
            return ('voice', res.status_code, res.text)

        def call_image():
            res = requests.post(
                IMAGE_URL,
                headers={
                    'Authorization': f'Bearer {BEARER}',
                    'Content-Type': 'application/json'
                },
                json={'script_id': script_id},
                timeout=120
            )
            return ('image', res.status_code, res.text)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(call_voice), executor.submit(call_image)]
            for future in as_completed(futures):
                label, status, body = future.result()
                print(f'[Pipeline] {label} worker: {status} - {body[:200]}')

        # Step 3: Poll for completion
        print('[Pipeline] Step 3: Polling for voice and image completion...')
        max_wait = 300
        poll_interval = 10
        elapsed = 0
        voice_ready = False
        image_ready = False

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
            print(f'[Pipeline] Timeout waiting for assets. voice: {voice_ready}, image: {image_ready}')
            return

        # Step 4: Assemble
        print('[Pipeline] Step 4: Assembling video...')
        video_record = get_video_record(script_id)
        script = get_script(script_id)

        outro_sound_url = get_outro_sound_url(SUPABASE_URL, SUPABASE_KEY)
        typewriter_sound_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'typewriter_sound_url')
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

        if typewriter_sound_url:
            try:
                typewriter_sound_path = download_file(typewriter_sound_url, '.mp3')
            except Exception as e:
                print(f'[Pipeline] Typewriter sound download failed: {e}')

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

        output_path = tempfile.mktemp(suffix='.mp4')

        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)
        setup_text = script.get('setup', None)

        assemble_video(image_path, audio_path, lines, output_path, setup_text, outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path)

        video_url = upload_video(script_id, output_path)
        update_video_record(script_id, video_url)

        print(f'[Pipeline] Done. Video URL: {video_url}')

        # Step 5: Publish to YouTube
        if YT_CLIENT_ID and YT_CLIENT_SECRET and YT_REFRESH_TOKEN:
            print('[Pipeline] Step 5: Publishing to YouTube...')
            publish_to_youtube_job(script_id)
        else:
            print('[Pipeline] YouTube credentials not set. Skipping YouTube publish.')

        # Step 6: Publish to Instagram
        if IG_ACCESS_TOKEN and IG_ACCOUNT_ID:
            print('[Pipeline] Step 6: Publishing to Instagram...')
            ig_media_id = publish_to_instagram_job(script_id)
            if ig_media_id:
                print(f'[Pipeline] Instagram published: {ig_media_id}')
            else:
                print('[Pipeline] Instagram publish returned no media ID (check logs above).')
        else:
            print('[Pipeline] Instagram credentials not set. Skipping Instagram publish.')

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

    return jsonify({
        'status': 'Publish complete',
        'script_id': script_id
    }), 200


@app.route('/publish-instagram', methods=['POST'])
def publish_instagram():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    script_id = data.get('script_id')

    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400

    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        return jsonify({'error': 'IG_ACCESS_TOKEN or IG_ACCOUNT_ID not set in Render environment'}), 500

    media_id = publish_to_instagram_job(script_id)

    if media_id:
        return jsonify({
            'success': True,
            'media_id': media_id,
            'script_id': script_id
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Instagram publish failed — check Render logs',
            'script_id': script_id
        }), 500


@app.route('/assemble', methods=['POST'])
def assemble():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    script_id = data.get('script_id')

    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400

    image_path = None
    audio_path = None
    output_path = None

    try:
        video_record = get_video_record(script_id)
        script = get_script(script_id)

        outro_sound_url = get_outro_sound_url(SUPABASE_URL, SUPABASE_KEY)
        typewriter_sound_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'typewriter_sound_url')
        outro_bg_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'outro_bg_url')
        logo_url = get_setting(SUPABASE_URL, SUPABASE_KEY, 'logo_url')

        image_url = video_record.get('image_url')
        audio_url = video_record.get('voice_file_url')

        if not image_url:
            return jsonify({'error': 'No image found for this script'}), 400
        if not audio_url:
            return jsonify({'error': 'No audio found for this script'}), 400

        image_path = download_file(image_url, '.jpg')
        audio_path = download_file(audio_url, '.mp3')

        outro_sound_path = None
        if outro_sound_url:
            try:
                outro_sound_path = download_file(outro_sound_url, '.mp3')
            except Exception as e:
                print(f'Outro sound download failed: {e}')

        typewriter_sound_path = None
        if typewriter_sound_url:
            try:
                typewriter_sound_path = download_file(typewriter_sound_url, '.mp3')
            except Exception as e:
                print(f'Typewriter sound download failed: {e}')

        outro_bg_path = None
        if outro_bg_url:
            try:
                outro_bg_path = download_file(outro_bg_url, '.jpg')
                print(f'Outro bg downloaded: {outro_bg_path}, exists: {os.path.exists(outro_bg_path) if outro_bg_path else False}')
            except Exception as e:
                print(f'Outro bg download failed: {e}')
        else:
            print('Outro bg URL not found in settings')

        logo_path = None
        if logo_url:
            try:
                logo_path = download_file(logo_url, '.png')
                print(f'Logo downloaded: {logo_path}')
            except Exception as e:
                print(f'Logo download failed: {e}')

        output_path = tempfile.mktemp(suffix='.mp4')

        lines = script.get('lines', [])
        if isinstance(lines, str):
            import json
            lines = json.loads(lines)
        setup_text = script.get('setup', None)
        print(f"Setup text: {setup_text}")
        print(f"Lines: {lines}")

        assemble_video(image_path, audio_path, lines, output_path, setup_text, outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path)

        video_url = upload_video(script_id, output_path)
        update_video_record(script_id, video_url)

        return jsonify({
            'success': True,
            'script_id': script_id,
            'video_url': video_url
        })

    except Exception as e:
        import traceback
        print(f"Assembly error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

    finally:
        for path in [image_path, audio_path, output_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
