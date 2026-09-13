import subprocess
import os

BGM_VOLUME = 0.1  # Volume for background music (10% of original volume)


def create_short_video(
    input_video_path: str,
    audio_path: str,
    bgm_path: str | None = None,
    subtitles_path: str | None = None,
    sfx_events: list[dict] = None,
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

    # Add VHS glitch visual effect synced with sound effects
    if sfx_events:
        enable_conditions = []
        for sfx in sfx_events:
            start_t = sfx["time"]
            end_t = start_t + 0.3  # Glitch duration: 300ms
            enable_conditions.append(f"between(t,{start_t},{end_t})")
            
        if enable_conditions:
            cond_str = "+".join(enable_conditions)
            # rgbashift separates red/blue for chromatic aberration, noise adds static grain
            v_filter += f",rgbashift=rh=30:bv=-30:enable='{cond_str}'"
            v_filter += f",noise=alls=60:allf=t+u:enable='{cond_str}'"

    # Handle audio inputs and mixing
    audio_inputs = []
    filter_complex_parts = [f"[0:v]{v_filter}[v]"]
    mix_elements = ["[1:a]"]
    
    input_idx = 2

    if bgm_path:
        # Loop the BGM indefinitely, we'll cut it off when the TTS audio ends
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])
        filter_complex_parts.append(f"[{input_idx}:a]volume={BGM_VOLUME}[bgm]")
        mix_elements.append("[bgm]")
        input_idx += 1
        
    if sfx_events:
        for i, sfx in enumerate(sfx_events):
            cmd.extend(["-i", sfx["file_path"]])
            delay_ms = int(sfx["time"] * 1000)
            # Use adelay filter. all=1 applies the delay to all channels.
            filter_complex_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[sfx{i}]")
            mix_elements.append(f"[sfx{i}]")
            input_idx += 1

    if len(mix_elements) > 1:
        mix_str = "".join(mix_elements) + f"amix=inputs={len(mix_elements)}:duration=first:normalize=0[a]"
        filter_complex_parts.append(mix_str)
        filter_complex = ";".join(filter_complex_parts)
        
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]"
        ])
    else:
        # No BGM and No SFX
        cmd.extend([
            "-filter:v", v_filter,
            "-map", "0:v:0",
            "-map", "1:a:0"
        ])

    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-pix_fmt",
            "yuv420p",
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
