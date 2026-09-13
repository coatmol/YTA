import subprocess
import os

BGM_VOLUME = 0.1  # Volume for background music (10% of original volume)


def create_short_video(
    input_video_path: str,
    audio_path: str,
    bgm_path: str | None = None,
    subtitles_path: str | None = None,
    sfx_events: list[dict] | None = None,
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

    filter_complex_parts = []

    # 1. Base video: crop to 9:16
    filter_complex_parts.append("[0:v]crop=ih*(9/16):ih[cropped]")

    # 2. Focus pull effect (1 second)
    filter_complex_parts.append("[cropped]split[sharp][for_blur]")
    filter_complex_parts.append("[for_blur]boxblur=10:10[blurred]")
    # Blend sharp (A) and blurred (B). At T=0, B is 100%. At T=1, A is 100%.
    filter_complex_parts.append(
        "[sharp][blurred]blend=all_expr='A*T + B*(1-T)':enable='between(t,0,1)'[focused]"
    )

    current_v = "[focused]"

    # 3. Subtitles
    if subtitles_path:
        sub_path_escaped = subtitles_path.replace("\\", "/")
        filter_complex_parts.append(f"{current_v}ass='{sub_path_escaped}'[with_subs]")
        current_v = "[with_subs]"

    # 4. SFX VHS Glitch
    if sfx_events:
        enable_conditions = []
        for sfx in sfx_events:
            start_t = sfx["time"]
            end_t = start_t + 0.3  # Glitch duration: 300ms
            enable_conditions.append(f"between(t,{start_t},{end_t})")

        if enable_conditions:
            cond_str = "+".join(enable_conditions)
            glitch_filters = f"rgbashift=rh=30:bv=-30:enable='{cond_str}',noise=alls=60:allf=t+u:enable='{cond_str}'"
            filter_complex_parts.append(f"{current_v}{glitch_filters}[with_glitch]")
            current_v = "[with_glitch]"

    # Guarantee pixel format and set final video tag
    filter_complex_parts.append(f"{current_v}format=yuv420p[v]")

    # Handle audio inputs and mixing
    audio_inputs = []
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
            filter_complex_parts.append(
                f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[sfx{i}]"
            )
            mix_elements.append(f"[sfx{i}]")
            input_idx += 1

    if len(mix_elements) > 1:
        mix_str = (
            "".join(mix_elements)
            + f"amix=inputs={len(mix_elements)}:duration=first:normalize=0[a]"
        )
        filter_complex_parts.append(mix_str)
        audio_map = "[a]"
    else:
        # Just map the TTS directly if no mixing is needed
        audio_map = "1:a:0"

    filter_complex = ";".join(filter_complex_parts)

    cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", audio_map])

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
