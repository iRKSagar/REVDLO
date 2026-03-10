import os
import subprocess
import uuid

# ----------------------------------------------------
# Configuration
# ----------------------------------------------------

FPS = 30
WIDTH = 1080
HEIGHT = 1920


# ----------------------------------------------------
# Utility
# ----------------------------------------------------

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)


# ----------------------------------------------------
# Background Motion (Ken Burns)
# ----------------------------------------------------

def create_motion_background(image_path, duration, output):

    zoom = "zoom+0.0006"

    cmd = f"""
    ffmpeg -y -loop 1 -i {image_path} \
    -vf "zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={WIDTH}x{HEIGHT},fps={FPS}" \
    -t {duration} \
    -c:v libx264 \
    -pix_fmt yuv420p \
    {output}
    """

    run(cmd)


# ----------------------------------------------------
# Atmosphere Overlay
# ----------------------------------------------------

def add_atmosphere(background_video, overlay_video, output):

    cmd = f"""
    ffmpeg -y \
    -stream_loop -1 -i {overlay_video} \
    -i {background_video} \
    -filter_complex "[0:v]scale={WIDTH}:{HEIGHT}[overlay];
                     [1:v][overlay]blend=all_mode='overlay':all_opacity=0.25" \
    -t 30 \
    -c:v libx264 \
    -pix_fmt yuv420p \
    {output}
    """

    run(cmd)


# ----------------------------------------------------
# Avatar Overlay
# ----------------------------------------------------

def add_avatar(background_video, avatar_video, output):

    cmd = f"""
    ffmpeg -y \
    -i {background_video} \
    -i {avatar_video} \
    -filter_complex "[1:v]scale=640:-1[avatar];
                     [0:v][avatar]overlay=(W-w)/2:H-h-120" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -shortest \
    {output}
    """

    run(cmd)


# ----------------------------------------------------
# Subtitles
# ----------------------------------------------------

def add_subtitles(video, srt_file, output):

    cmd = f"""
    ffmpeg -y \
    -i {video} \
    -vf subtitles={srt_file}:force_style='Fontsize=48,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,BorderStyle=3,Outline=2' \
    -c:v libx264 \
    -pix_fmt yuv420p \
    {output}
    """

    run(cmd)


# ----------------------------------------------------
# Outro Card
# ----------------------------------------------------

def add_outro(video, outro_image, output):

    outro_clip = f"/tmp/outro_{uuid.uuid4().hex}.mp4"

    cmd1 = f"""
    ffmpeg -y -loop 1 -i {outro_image} \
    -t 4 \
    -vf scale={WIDTH}:{HEIGHT} \
    -c:v libx264 \
    -pix_fmt yuv420p \
    {outro_clip}
    """

    run(cmd1)

    cmd2 = f"""
    ffmpeg -y \
    -i {video} \
    -i {outro_clip} \
    -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    {output}
    """

    run(cmd2)


# ----------------------------------------------------
# Assembly Pipeline
# ----------------------------------------------------

def assemble_video(
        background_image,
        avatar_video,
        subtitles_file,
        outro_image,
        overlay_video=None,
        duration=25):

    uid = uuid.uuid4().hex

    motion_bg = f"/tmp/bg_motion_{uid}.mp4"
    atmosphere = f"/tmp/bg_atmos_{uid}.mp4"
    avatar_layer = f"/tmp/avatar_{uid}.mp4"
    subtitles_layer = f"/tmp/subs_{uid}.mp4"
    final_output = f"final_video_{uid}.mp4"

    # 1 motion background
    create_motion_background(background_image, duration, motion_bg)

    # 2 atmosphere
    if overlay_video:
        add_atmosphere(motion_bg, overlay_video, atmosphere)
    else:
        atmosphere = motion_bg

    # 3 avatar overlay
    add_avatar(atmosphere, avatar_video, avatar_layer)

    # 4 subtitles
    if subtitles_file:
        # subtitles temporarily disabled
        subtitles_layer = avatar_layer
    else:
        subtitles_layer = avatar_layer

    # 5 outro
    add_outro(subtitles_layer, outro_image, final_output)

    return final_output


# ----------------------------------------------------
# Example Run
# ----------------------------------------------------

if __name__ == "__main__":

    video = assemble_video(
        background_image="background.png",
        avatar_video="avatar.mp4",
        subtitles_file="captions.srt",
        outro_image="outro.png",
        overlay_video="dust_overlay.mov"
    )

    print("Video created:", video)
