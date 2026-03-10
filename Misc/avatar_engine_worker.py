import modal

app = modal.App("avatar-engine")

# ----------------------------------------------------
# GPU Image
# ----------------------------------------------------

image = (
    modal.Image.from_registry(
        "nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04",
        add_python="3.10"
    )
    .env({"DEBIAN_FRONTEND": "noninteractive"})
    .apt_install(
        "git",
        "ffmpeg",
        "wget",
        "libgl1-mesa-glx",
        "sox",
        "libsox-fmt-all"
    )
    .pip_install(
        "torch==1.13.1+cu116",
        "torchvision==0.14.1+cu116",
        extra_index_url="https://download.pytorch.org/whl/cu116"
    )
    .pip_install(
        "numpy==1.23.5",
        "opencv-python-headless==4.10.0.84",
        "librosa==0.8.1",
        "numba==0.56.4",
        "scipy",
        "tqdm",
        "Pillow",
        "soundfile",
        "audioread"
    )
    .run_commands(
        "git clone https://github.com/Rudrabha/Wav2Lip /wav2lip",
        "mkdir -p /wav2lip/checkpoints",
        "wget https://github.com/justinjohn0306/Wav2Lip/releases/download/models/wav2lip_gan.pth -O /wav2lip/checkpoints/wav2lip_gan.pth"
    )
)

# ----------------------------------------------------
# Avatar Engine Worker
# ----------------------------------------------------

@app.function(
    image=image,
    gpu="T4",
    timeout=1800,
    memory=8192
)
def generate_avatar(image_bytes: bytes, audio_bytes: bytes) -> bytes:

    import os
    import tempfile
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:

        avatar_path = os.path.join(tmp, "avatar.png")
        audio_input = os.path.join(tmp, "audio_input")
        audio_path = os.path.join(tmp, "audio.wav")
        base_video = os.path.join(tmp, "base.mp4")
        output_video = os.path.join(tmp, "output.mp4")

        # ------------------------------------------------
        # Save input files
        # ------------------------------------------------

        with open(avatar_path, "wb") as f:
            f.write(image_bytes)

        with open(audio_input, "wb") as f:
            f.write(audio_bytes)

        # ------------------------------------------------
        # Convert audio to 16k mono wav
        # ------------------------------------------------

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                audio_input,
                "-ac",
                "1",
                "-ar",
                "16000",
                audio_path
            ],
            check=True
        )

        # ------------------------------------------------
        # Create base avatar video from image
        # ------------------------------------------------

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                avatar_path,
                "-t",
                "5",
                "-vf",
                "scale=512:512",
                "-pix_fmt",
                "yuv420p",
                base_video
            ],
            check=True
        )

        # ------------------------------------------------
        # Run Wav2Lip
        # ------------------------------------------------

        subprocess.run(
            [
                "python",
                "/wav2lip/inference.py",
                "--checkpoint_path",
                "/wav2lip/checkpoints/wav2lip_gan.pth",
                "--face",
                base_video,
                "--audio",
                audio_path,
                "--outfile",
                output_video
            ],
            cwd="/wav2lip",
            check=True
        )

        # ------------------------------------------------
        # Return generated video
        # ------------------------------------------------

        with open(output_video, "rb") as f:
            return f.read()
