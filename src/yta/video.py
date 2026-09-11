import subprocess
import os


def create_short_video(
    input_video_path: str,
    audio_path: str,
    bgm_path: str | None = None,
    output_path: str = "final_short.mp4",
):
    """
    Crops the input video to a 9:16 aspect ratio (centered) and replaces
    its audio with the given TTS audio file. Optionally mixes in background music.
    """
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video not found: {input_video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if bgm_path and not os.path.exists(bgm_path):
        raise FileNotFoundError(f"BGM file not found: {bgm_path}")

    print(f"Processing video: {input_video_path}...")
    print("Cropping to 9:16 and merging with TTS audio (this may take a moment)...")

    cmd = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i",
        input_video_path,
        "-i",
        audio_path,
    ]

    if bgm_path:
        # Loop the BGM indefinitely, we'll cut it off when the TTS audio ends
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])

        # [0:v] crop to 9:16
        # [2:a] lower BGM volume to 10%
        # [1:a][bgm] mix TTS and BGM. duration=first ensures the mix ends when TTS ends.
        # normalize=0 ensures the TTS volume doesn't get quieted by the mixer.
        filter_complex = (
            "[0:v]crop=ih*(9/16):ih[v];"
            "[2:a]volume=0.1[bgm];"
            "[1:a][bgm]amix=inputs=2:duration=first:normalize=0[a]"
        )
        cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-map",
                "[v]",
                "-map",
                "[a]",
            ]
        )
    else:
        cmd.extend(
            [
                "-filter:v",
                "crop=ih*(9/16):ih",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
            ]
        )

    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            output_path,
        ]
    )

    try:
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"Successfully created final video: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while processing video: {e}")
        raise e
