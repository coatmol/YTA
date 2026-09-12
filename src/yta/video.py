import subprocess
import os

BGM_VOLUME = 0.1  # Volume for background music (10% of original volume)


def create_short_video(
    input_video_path: str,
    audio_path: str,
    bgm_path: str | None = None,
    subtitles_path: str | None = None,
    output_path: str = "final_short.mp4",
):
    """
    Crops the input video to a 9:16 aspect ratio (centered), replaces
    its audio with the given TTS audio file, and burns in ASS subtitles.
    Optionally mixes in background music.
    """
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video not found: {input_video_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if bgm_path and not os.path.exists(bgm_path):
        raise FileNotFoundError(f"BGM file not found: {bgm_path}")
    if subtitles_path and not os.path.exists(subtitles_path):
        raise FileNotFoundError(f"Subtitles file not found: {subtitles_path}")

    print(f"Processing video: {input_video_path}...")
    print(
        "Cropping to 9:16, burning subtitles, and merging audio (this may take a moment)..."
    )

    cmd = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i",
        input_video_path,
        "-i",
        audio_path,
    ]

    # Base video filter: crop to 9:16
    v_filter = "crop=ih*(9/16):ih"

    # If subtitles are provided, burn them in after cropping
    if subtitles_path:
        # We must escape backslashes and colons in the path for ffmpeg filter syntax
        # Using forward slashes is safer for ffmpeg paths on Windows
        sub_path_escaped = subtitles_path.replace("\\", "/")
        v_filter += f",ass='{sub_path_escaped}'"

    if bgm_path:
        # Loop the BGM indefinitely, we'll cut it off when the TTS audio ends
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])

        # [0:v] crop and add subtitles
        # [2:a] lower BGM volume to 15%
        # [1:a][bgm] mix TTS and BGM
        filter_complex = (
            f"[0:v]{v_filter}[v];"
            "[2:a]volume=0.15[bgm];"
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
                v_filter,
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
