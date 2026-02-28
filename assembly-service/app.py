import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os
import requests
import tempfile
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, TextClip
)
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


def check_auth(req):
    auth = req.headers.get('Authorization', '')
    return auth == f'Bearer {COUNCIL_SECRET}'


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

    # Step 1: Initialize resumable upload
    metadata = {
        'snippet': {
            'title': title[:100],
            'description': description,
            'tags': tags,
            'categoryId': '22'  # People & Blogs
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

    # Step 2: Upload video bytes
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

        # Get video record
        video_record = get_video_record(script_id)
        video_url = video_record.get('video_url')
        if not video_url:
            print(f'[Publish] No video_url found for script {script_id}')
            return

        # Get script for title and lines
        script = get_script(script_id)
        setup = script.get('setup', 'Mr. Oldverdict')
        lines = script.get('lines', [])
        if isinstance(lines, str):
            lines = json.loads(lines)

        # Build YouTube title and description
        title = setup[:93] + ' #Shorts'
        line1 = strip_emotion_tags(lines[0]['text']) if lines else ''
        line2 = lines[1]['text'] if len(lines) > 1 else ''
        description = f'{line1}\n\n{line2}\n\n#mroldverdict #Shorts #comedy #wisdom #observations'

        tags = ['mroldverdict', 'shorts', 'comedy', 'wisdom', 'observations', 'oldverdict']

        # Download video
        print(f'[Publish] Downloading video from Supabase...')
        video_path = download_file(video_url, '.mp4')

        # Upload to YouTube
        print(f'[Publish] Uploading to YouTube...')
        yt_id = upload_to_youtube(video_path, title, description, tags)
        print(f'[Publish] YouTube video ID: {yt_id}')

        # Mark published
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
    import re
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
            w *= 1.4
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


def build_setup_card(setup_text, video_width, video_height, image_path=None, duration=5.0, typewriter_sound_path=None, logo_path=None):
    """Build a typewriter-effect setup card with optional background image."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, ImageClip, concatenate_videoclips
        import numpy as np

        if image_path and os.path.exists(image_path):
            bg_img = ImageClip(image_path).resize((video_width, video_height))
            dark_overlay = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).set_opacity(0.82)
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
            clip_start = 0.5 + (i * char_interval)
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
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    target_width = 540
    target_height = 960

    image_clip = ImageClip(image_path).set_duration(duration)

    img_w, img_h = image_clip.size
    scale = max(target_width / img_w, target_height / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    image_clip = image_clip.resize((new_w, new_h))

    image_clip = crop(
        image_clip,
        width=target_width,
        height=target_height,
        x_center=new_w / 2,
        y_center=new_h / 2
    )

    from moviepy.editor import ColorClip
    dark_band = (ColorClip(size=(target_width, 400), color=(0, 0, 0))
                 .set_opacity(0.55)
                 .set_position((0, target_height - 450))
                 .set_duration(duration))

    caption_clips = build_caption_clips(lines, duration, target_width, target_height)

    try:
        watermark = (TextClip(
            "@mroldverdict",
            fontsize=24,
            color='white',
            font='DejaVu-Serif',
            method='label'
        )
        .set_opacity(0.45)
        .set_position((target_width - 180, target_height - 50))
        .set_duration(audio.duration))
        main_layers = [image_clip, dark_band] + caption_clips + [watermark]
    except Exception as e:
        print(f'Watermark failed: {e}')
        main_layers = [image_clip, dark_band] + caption_clips

    audio_faded = audio.audio_fadein(0.4).audio_fadeout(0.5)

    pre_hold = 1.0
    post_hold = 2.0
    total_image_duration = pre_hold + duration + post_hold

    from moviepy.audio.AudioClip import AudioClip, concatenate_audioclips
    import numpy as np
    silence_pre = AudioClip(lambda t: np.zeros(2), duration=pre_hold, fps=44100)
    silence_post = AudioClip(lambda t: np.zeros(2), duration=post_hold, fps=44100)
    extended_audio = concatenate_audioclips([silence_pre, audio_faded, silence_post])

    image_clip = image_clip.set_duration(total_image_duration)
    dark_band = dark_band.set_duration(pre_hold + duration).set_start(0)
    caption_clips = [c.set_start(c.start + pre_hold) for c in caption_clips]

    try:
        watermark = watermark.set_duration(total_image_duration)
        main_layers = [image_clip, dark_band] + caption_clips + [watermark]
    except:
        main_layers = [image_clip, dark_band] + caption_clips

    main_clip = CompositeVideoClip(main_layers, size=(target_width, target_height))
    main_clip = main_clip.fadein(0.8).set_audio(extended_audio).set_duration(total_image_duration).fadeout(0.6)

    from moviepy.editor import concatenate_videoclips, ColorClip as _ColorClip
    clips = []

    if setup_text:
        setup_card = build_setup_card(setup_text, target_width, target_height, image_path=image_path, duration=5.0, typewriter_sound_path=typewriter_sound_path, logo_path=logo_path)
        if setup_card:
            setup_card = setup_card.fadeout(0.8)
            clips.append(setup_card)

    clips.append(main_clip)

    fade_gap = _ColorClip(size=(target_width, target_height), color=(0,0,0)).set_duration(1.5)
    clips.append(fade_gap)

    outro_audio_path = outro_sound_path
    outro_card = build_outro_card(target_width, target_height, outro_audio_path=outro_audio_path, duration=3.5, image_path=outro_bg_path, logo_path=logo_path)
    if outro_card:
        outro_card = outro_card.fadein(0.5)
        clips.append(outro_card)

    if len(clips) > 1:
        final = concatenate_videoclips(clips)
    else:
        final = main_clip

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
    """
    Full automated pipeline:
    1. Call council (auto-selects topic from queue)
    2. Call voice + image simultaneously
    3. Poll until both are ready
    4. Assemble video
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
        # Step 1: Council - auto-select topic (empty body)
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

        # Step 3: Poll videos table until both voice_file_url and image_url are populated
        print('[Pipeline] Step 3: Polling for voice and image completion...')
        import time
        max_wait = 300  # 5 minutes
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
            print('[Pipeline] YouTube credentials not set. Skipping publish.')
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


@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'Assembly service standing by.'})


@app.route('/run-pipeline', methods=['POST'])
def run_pipeline():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    # Fire pipeline in background thread - return 202 immediately
    thread = threading.Thread(target=run_pipeline_job, daemon=True)
    thread.start()

    return jsonify({
        'status': 'Pipeline started',
        'message': 'Council → Voice + Image → Assembly running in background'
    }), 202


@app.route('/publish', methods=['POST'])
def publish():
    if not check_auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    script_id = data.get('script_id')

    if not script_id:
        return jsonify({'error': 'script_id is required'}), 400

    # Run synchronously — Render can hold the connection
    publish_to_youtube_job(script_id)

    return jsonify({
        'status': 'Publish complete',
        'script_id': script_id
    }), 200


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
