import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import os
import requests
import tempfile
import json
from flask import Flask, request, jsonify
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip, TextClip
)
from moviepy.video.fx.all import crop

app = Flask(__name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
COUNCIL_SECRET = os.environ.get('COUNCIL_SECRET')


def check_auth(req):
    auth = req.headers.get('Authorization', '')
    return auth == f'Bearer {COUNCIL_SECRET}'


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

    # Use character count as proxy for speech time to sync captions with voice
    # Strip emotion tags to get actual spoken text length
    cleaned = [strip_emotion_tags(l.get('text', '')) for l in lines]
    char_counts = [max(len(t), 1) for t in cleaned]
    # Add weight for pause_after lines (they have trailing ellipsis in audio)
    weights = []
    for i, line in enumerate(lines):
        w = char_counts[i]
        if line.get('pause_after', False):
            w *= 1.4  # pause after adds roughly 40% more time
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

        # Background - darkened character image if available
        if image_path and os.path.exists(image_path):
            bg_img = ImageClip(image_path).resize((video_width, video_height)).set_duration(duration)
            dark_overlay = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).set_opacity(0.75).set_duration(duration)
            bg = CompositeVideoClip([bg_img, dark_overlay], size=(video_width, video_height))
        else:
            bg = ColorClip(size=(video_width, video_height), color=(10, 10, 10)).set_duration(duration)

        # Channel name
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

        # Tagline
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

        # Daily dose line
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

        # Follow line
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

        # Logo top left on outro
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

        # Add outro sound if available
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

        # Build background - darkened image if available, else dark color
        if image_path and os.path.exists(image_path):
            bg_img = ImageClip(image_path).resize((video_width, video_height))
            # Darken the image heavily so text reads clearly
            dark_overlay = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).set_opacity(0.82)
            bg_base = CompositeVideoClip([bg_img, dark_overlay], size=(video_width, video_height))
        else:
            bg_base = ColorClip(size=(video_width, video_height), color=(15, 15, 15))

        # Typewriter effect - reveal text character by character
        # Split duration: first 0.5s empty, then type out, last 1s full text
        chars = list(setup_text)
        total_chars = len(chars)
        type_duration = duration - 1.5  # time to type out all chars
        char_interval = type_duration / max(total_chars, 1)

        frames_clips = []

        # No label - logo replaces it

        # Build typewriter frames - one clip per character reveal
        # Group into chunks to keep clip count manageable
        chunk_size = max(1, total_chars // 20)
        shown_chars = 0
        last_end = 0.5  # start typing after 0.5s

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

        # Final full text for remaining duration
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

        # Logo in top left corner
        logo_clips = []
        if logo_path and os.path.exists(logo_path):
            try:
                logo_img = (ImageClip(logo_path)
                    .resize(height=100)
                    .set_position((20, 20))
                    .set_duration(duration))
                logo_clips = [logo_img]
            except Exception as e:
                print(f'Logo on setup card failed: {e}')

        all_clips = [bg_clip] + logo_clips + frames_clips + [final_txt]
        card = CompositeVideoClip(all_clips, size=(video_width, video_height)).set_duration(duration)

        # Add typewriter sound synced to typing - starts at 0.5s when text begins appearing
        if typewriter_sound_path and os.path.exists(typewriter_sound_path):
            try:
                from moviepy.editor import AudioFileClip as _AFC
                from moviepy.audio.AudioClip import concatenate_audioclips
                tw_single = _AFC(typewriter_sound_path)
                type_dur = last_end - 0.5
                loops_needed = int(type_dur / tw_single.duration) + 2
                looped = concatenate_audioclips([tw_single] * loops_needed)
                tw_trimmed = looped.subclip(0, type_dur).audio_fadeout(0.4)
                # Offset audio to start at 0.5s to match when text starts appearing
                tw_trimmed = tw_trimmed.set_start(0.5)
                card = card.set_audio(tw_trimmed)
            except Exception as e:
                print(f'Typewriter audio failed: {e}')

        return card

    except Exception as e:
        print(f'Setup card failed: {e}')
        return None


def assemble_video(image_path, audio_path, lines, output_path, setup_text=None, outro_sound_path=None, typewriter_sound_path=None, outro_bg_path=None, logo_path=None):
    # Load audio to get duration
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Target: 9:16 vertical format for Shorts and Reels
    target_width = 540
    target_height = 960

    # Load and resize image to fill 9:16
    image_clip = ImageClip(image_path).set_duration(duration)

    # Scale image to fill the frame
    img_w, img_h = image_clip.size
    scale = max(target_width / img_w, target_height / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    image_clip = image_clip.resize((new_w, new_h))

    # Crop to exact 9:16
    image_clip = crop(
        image_clip,
        width=target_width,
        height=target_height,
        x_center=new_w / 2,
        y_center=new_h / 2
    )

    # Add dark gradient overlay at bottom for caption readability
    # Simple dark band using a semi transparent image
    from moviepy.editor import ColorClip
    dark_band = (ColorClip(size=(target_width, 400), color=(0, 0, 0))
                 .set_opacity(0.55)
                 .set_position((0, target_height - 450))
                 .set_duration(duration))

    # Build caption clips
    caption_clips = build_caption_clips(lines, duration, target_width, target_height)

    # Watermark
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

    # Fade in audio so voice does not hit hard on the ears
    audio_faded = audio.audio_fadein(0.4).audio_fadeout(0.5)

    # Video structure:
    # Phase 1: 1 second image with no voice, no captions (pre-voice hold)
    # Phase 2: voice duration with captions
    # Phase 3: 2 seconds image with no captions (post-voice hold)
    pre_hold = 1.0
    post_hold = 2.0
    total_image_duration = pre_hold + duration + post_hold

    # Extend audio with silence for pre and post holds
    from moviepy.audio.AudioClip import AudioClip, concatenate_audioclips
    import numpy as np
    silence_pre = AudioClip(lambda t: np.zeros(2), duration=pre_hold, fps=44100)
    silence_post = AudioClip(lambda t: np.zeros(2), duration=post_hold, fps=44100)
    extended_audio = concatenate_audioclips([silence_pre, audio_faded, silence_post])

    # Image covers full duration
    image_clip = image_clip.set_duration(total_image_duration)

    # Dark band only during pre-hold + voice section, fades out before post-voice hold
    dark_band = dark_band.set_duration(pre_hold + duration).set_start(0)

    # Captions start at pre_hold and run for voice duration only
    caption_clips = [c.set_start(c.start + pre_hold) for c in caption_clips]

    # Watermark covers full image duration
    try:
        watermark = watermark.set_duration(total_image_duration)
        main_layers = [image_clip, dark_band] + caption_clips + [watermark]
    except:
        main_layers = [image_clip, dark_band] + caption_clips

    main_clip = CompositeVideoClip(main_layers, size=(target_width, target_height))
    # Fade in from dark - brightness reveal as voice starts
    main_clip = main_clip.fadein(0.8).set_audio(extended_audio).set_duration(total_image_duration).fadeout(0.6)

    # Add setup card at the start and outro card at the end
    from moviepy.editor import concatenate_videoclips, ColorClip as _ColorClip
    clips = []

    if setup_text:
        setup_card = build_setup_card(setup_text, target_width, target_height, image_path=image_path, duration=5.0, typewriter_sound_path=typewriter_sound_path, logo_path=logo_path)
        if setup_card:
            # Fade out setup card so main video fades in bright
            setup_card = setup_card.fadeout(0.8)
            clips.append(setup_card)

    clips.append(main_clip)

    # 1.5 second fade to black before outro
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

    # Write video
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


@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'Assembly service standing by.'})


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
        # Get video record with image and audio URLs
        video_record = get_video_record(script_id)
        script = get_script(script_id)

        # Fetch outro and typewriter sound URLs
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

        # Download image and audio
        image_path = download_file(image_url, '.jpg')
        audio_path = download_file(audio_url, '.mp3')

        # Download outro and typewriter sounds if available
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

        # Output path
        output_path = tempfile.mktemp(suffix='.mp4')

        # Read directly from script columns
        lines = script.get('lines', [])
        if isinstance(lines, str):
            import json
            lines = json.loads(lines)
        setup_text = script.get('setup', None)
        print(f"Setup text: {setup_text}")
        print(f"Lines: {lines}")

        # Assemble video
        assemble_video(image_path, audio_path, lines, output_path, setup_text, outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path)

        # Upload to Supabase
        video_url = upload_video(script_id, output_path)

        # Update video record
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
        # Clean up temp files
        for path in [image_path, audio_path, output_path, outro_sound_path, typewriter_sound_path, outro_bg_path, logo_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
