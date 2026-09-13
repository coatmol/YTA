import subprocess
import os

BGM_VOLUME = 0.1  # Volume for background music (10% of original volume)


def create_short_video(
    input_video_path: str,
    audio_path: str,
    bgm_path: str | None = None,
    subtitles_path: str | None = None,
    sfx_events: list[dict] | None = None,
    character_events: list[dict] | None = None,
    output_path: str = "final_short.mp4",
):
    """
    Crops the input video to a 9:16 aspect ratio (centered), replaces
    its audio with the given TTS audio file, and burns in ASS subtitles.
    Optionally mixes in background music and character overlays.
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
        "Cropping to 9:16, burning subtitles, adding overlays, and merging audio (this may take a moment)..."
    )

    ffmpeg_command = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i",
        input_video_path,
        "-i",
        audio_path,
    ]

    input_idx = 2
    filter_complex_parts = []

    # Map character to file paths and track their input index
    char_images = {
        "Stewie": "assets/images/stewie.png",
        "Peter": "assets/images/peter.png"
    }
    char_input_map = {}

    if character_events:
        active_chars = {event["character"] for event in character_events}
        for char in active_chars:
            if char in char_images and os.path.exists(char_images[char]):
                ffmpeg_command.extend(["-i", char_images[char]])
                # scale image to a reasonable size, e.g. 400x400 max
                filter_complex_parts.append(f"[{input_idx}:v]scale=400:-1[img_{char}]")
                char_input_map[char] = f"[img_{char}]"
                input_idx += 1

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

    # 3. Add Character Images
    if character_events and char_input_map:
        for char_name, img_stream in char_input_map.items():
            # Find all intervals where this character speaks
            intervals = []
            for event in character_events:
                if event["character"] == char_name:
                    intervals.append(f"between(t,{event['start']},{event['end']})")
            
            if intervals:
                enable_str = "+".join(intervals)
                next_v = f"[v_overlay_{char_name}]"
                filter_complex_parts.append(
                    f"{current_v}{img_stream}overlay=20:H-h-20:enable='{enable_str}'{next_v}"
                )
                current_v = next_v

    # 4. Subtitles
    if subtitles_path:
        sub_path_escaped = subtitles_path.replace("\\", "/")
        filter_complex_parts.append(f"{current_v}ass='{sub_path_escaped}':fontsdir='assets/fonts'[with_subs]")
        current_v = "[with_subs]"

    # Guarantee pixel format and set final video tag
    filter_complex_parts.append(f"{current_v}format=yuv420p[v]")

    # Handle audio inputs and mixing
    audio_inputs = []
    mix_elements = ["[1:a]"]

    if bgm_path:
        # Loop the BGM indefinitely, we'll cut it off when the TTS audio ends
        ffmpeg_command.extend(["-stream_loop", "-1", "-i", bgm_path])
        filter_complex_parts.append(f"[{input_idx}:a]volume={BGM_VOLUME}[bgm]")
        mix_elements.append("[bgm]")
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

    ffmpeg_command.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", audio_map])

    ffmpeg_command.extend(
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
            ffmpeg_command, check=True, stdout=subprocess.DEVNULL
        )
        print(f"Successfully created final video: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while processing video: {e}")
        raise e
