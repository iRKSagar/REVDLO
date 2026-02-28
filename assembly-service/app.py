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
        f'{SUPABASE_URL}/rest/v1/scripts?id=eq.{script_id}&limit=1&select=*',
        headers={
            'apikey': SUPABASE_KEY,
            'Authorization': f'Bearer {SUPABASE_KEY}'
        }
    )
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception('Script not found')
    return data[0]


def strip_emotion_tags(text):
    """Remove emotion tags like [clears throat] [laughing] from caption text."""
    import re
    return re.sub(r'\[.*?\]', '', text).strip()


def build_caption_clips(lines, video_duration, video_width, video_height):
    caption_clips = []
    num_lines = len(lines)

    if num_lines == 0:
        return caption_clips

    # Divide video duration across lines
    # First line gets more time if it has pause_after
    segment_duration = video_duration / num_lines
    current_time = 0

    for i, line in enumerate(lines):
        text = strip_emotion_tags(line.get('text', ''))
        pause_after = line.get('pause_after', False)

        # Duration for this line
        if pause_after and i < num_lines - 1:
            duration = segment_duration * 1.3
        else:
            duration = segment_duration * 0.7 if i == num_lines - 1 else segment_duration

        # Clamp to video duration
        duration = min(duration, video_duration - current_time)
        if duration <= 0:
            break

        try:
            txt_clip = (TextClip(
                text,
                fontsize=42,
                color='white',
                font='DejaVu-Sans-Bold',
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


def build_outro_card(video_width, video_height, outro_audio_path=None, duration=3.0):
    """Build the outro card with Mr. Oldverdict branding."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip

        # Dark background
        bg = ColorClip(size=(video_width, video_height), color=(10, 10, 10)).set_duration(duration)

        # Channel name
        name_clip = (TextClip(
            "Mr. Oldverdict",
            fontsize=58,
            color='white',
            font='DejaVu-Sans-Bold',
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
            font='DejaVu-Sans',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.50))
        .set_duration(duration))

        # Handle
        handle_clip = (TextClip(
            "@mroldverdict",
            fontsize=28,
            color='#888888',
            font='DejaVu-Sans',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.58))
        .set_duration(duration))

        outro = CompositeVideoClip([bg, name_clip, tagline_clip, handle_clip], size=(video_width, video_height))

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


def build_setup_card(setup_text, video_width, video_height, duration=3.0):
    """Build a text card clip for the setup line."""
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip

        # Dark background card
        bg = ColorClip(size=(video_width, video_height), color=(15, 15, 15)).set_duration(duration)

        # Setup text
        txt = (TextClip(
            setup_text,
            fontsize=46,
            color='white',
            font='DejaVu-Sans',
            method='caption',
            size=(video_width - 120, None),
            align='center'
        )
        .set_position('center')
        .set_duration(duration))

        # Small label above
        label = (TextClip(
            "Been watching since before.",
            fontsize=28,
            color='#888888',
            font='DejaVu-Sans',
            method='label',
            align='center'
        )
        .set_position(('center', video_height * 0.35))
        .set_duration(duration))

        return CompositeVideoClip([bg, label, txt], size=(video_width, video_height))
    except Exception as e:
        print(f'Setup card failed: {e}')
        return None


def assemble_video(image_path, audio_path, lines, output_path, setup_text=None, outro_sound_path=None):
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
            font='DejaVu-Sans',
            method='label'
        )
        .set_opacity(0.45)
        .set_position((target_width - 180, target_height - 50))
        .set_duration(audio.duration))
        main_layers = [image_clip, dark_band] + caption_clips + [watermark]
    except Exception as e:
        print(f'Watermark failed: {e}')
        main_layers = [image_clip, dark_band] + caption_clips

    # Compose main video
    main_clip = CompositeVideoClip(main_layers, size=(target_width, target_height))
    main_clip = main_clip.set_audio(audio)

    # Add setup card at the start and outro card at the end
    from moviepy.editor import concatenate_videoclips
    clips = []

    if setup_text:
        setup_card = build_setup_card(setup_text, target_width, target_height, duration=3.0)
        if setup_card:
            clips.append(setup_card)

    clips.append(main_clip)

    outro_audio_path = outro_sound_path
    outro_card = build_outro_card(target_width, target_height, outro_audio_path=outro_audio_path, duration=3.0)
    if outro_card:
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

        # Fetch outro sound URL
        outro_sound_url = get_outro_sound_url(SUPABASE_URL, SUPABASE_KEY)

        image_url = video_record.get('image_url')
        audio_url = video_record.get('voice_file_url')

        if not image_url:
            return jsonify({'error': 'No image found for this script'}), 400
        if not audio_url:
            return jsonify({'error': 'No audio found for this script'}), 400

        # Download image and audio
        image_path = download_file(image_url, '.jpg')
        audio_path = download_file(audio_url, '.mp3')

        # Download outro sound if available
        outro_sound_path = None
        if outro_sound_url:
            try:
                outro_sound_path = download_file(outro_sound_url, '.mp3')
            except Exception as e:
                print(f'Outro sound download failed: {e}')

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
        assemble_video(image_path, audio_path, lines, output_path, setup_text, outro_sound_path)

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
        for path in [image_path, audio_path, output_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception:
                    pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
