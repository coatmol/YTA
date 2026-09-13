import json
import os
from PIL import ImageFont


def format_time(seconds: float) -> str:
    """Formats time in seconds to ASS time format: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_ass(word_timestamps_path: str, output_ass_path: str):
    """
    Reads word timestamps and generates an ASS subtitle file.
    Features:
    - Smart text wrapping by pixel width
    - Zero flickering (text drawn continuously per chunk)
    - Perfectly rounded red rectangle behind active word (using explicit baseline-anchored ASS vector drawings)
    """
    if not os.path.exists(word_timestamps_path):
        raise FileNotFoundError(f"Timestamps file not found: {word_timestamps_path}")

    with open(word_timestamps_path, "r", encoding="utf-8") as f:
        words = json.load(f)

    font_size = 130

    font = ImageFont.load_default()

    # PIL calculates widths based on Em size, but libass scales the font
    # so that the Ascent + Descent exactly matches the given FontSize.
    # We must apply this ratio so our widths match libass exactly.
    getmetrics = getattr(font, "getmetrics", None)
    if callable(getmetrics):
        asc, desc = getmetrics()  # type: ignore
        ass_scale = font_size / (asc + desc)
    else:
        ass_scale = 1.0

    space_width = font.getlength(" ") * ass_scale
    screen_w = 1080

    # We use Bottom-Left alignment (\an1) for text, so center_y represents the BASELINE.
    # We move it down slightly to 1010 to keep it vertically centered on the 1920 screen
    # considering the 130px font size.
    center_y = 1010

    # Group into chunks, wrapping by max pixel width or max 3 words
    chunks = []
    current_chunk = []
    current_width = 0
    max_width = screen_w - 150

    for w in words:
        w_text = w["word"].lower()
        w_width = font.getlength(w_text) * ass_scale

        if current_chunk:
            new_width = current_width + space_width + w_width
            if new_width > max_width or len(current_chunk) >= 3:
                chunks.append(current_chunk)
                current_chunk = [w]
                current_width = w_width
                continue

        current_chunk.append(w)
        if len(current_chunk) == 1:
            current_width = w_width
        else:
            current_width += space_width + w_width

        # Break chunk immediately if the word ends with punctuation (ignoring trailing quotes)
        has_punct = False
        for char in reversed(w_text):
            if char.isalnum():
                break
            if char in [".", ",", "!", "?", ":", ";"]:
                has_punct = True
                break

        if has_punct:
            chunks.append(current_chunk)
            current_chunk = []
            current_width = 0

    if current_chunk:
        chunks.append(current_chunk)

    # ASS Header
    # Inactive: BorderStyle=1, Outline=4
    # ActiveBox: BorderStyle=1, Outline=15 (Corner radius)
    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Inactive,Impact,130,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,0,1,0,0,500,1
Style: ActiveBox,Impact,130,&H000000FF,&H000000FF,&H000000FF,&H000000FF,-1,0,0,0,100,100,0,0,1,16,0,7,0,0,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []

    for idx, chunk in enumerate(chunks):
        word_widths = [font.getlength(w["word"].lower()) * ass_scale for w in chunk]
        total_width = sum(word_widths) + (space_width * (len(chunk) - 1))
        start_x = (screen_w - total_width) / 2

        if idx < len(chunks) - 1:
            next_chunk_start = chunks[idx + 1][0]["start"]
        else:
            next_chunk_start = 999999.0

        chunk_start_sec = chunk[0]["start"]
        chunk_end_sec = min(chunk[-1]["end"] + 0.1, next_chunk_start)

        chunk_start_time = format_time(chunk_start_sec)
        chunk_end_time = format_time(chunk_end_sec)

        # Layer 1: Draw the text for the ENTIRE chunk duration to completely eliminate flickering
        current_x = start_x
        for j, w in enumerate(chunk):
            word_text = w["word"].lower()
            # Explicitly force Alignment 1 (Bottom-Left) so baseline is exactly at center_y
            pos_tag = f"{{\\an1\\pos({current_x},{center_y})}}"
            events.append(
                f"Dialogue: 1,{chunk_start_time},{chunk_end_time},Inactive,,0,0,0,,{pos_tag}{word_text}"
            )
            current_x += word_widths[j] + space_width

        # Layer 0: Draw the perfectly rounded red rectangle ONLY during the active word
        current_x = start_x
        for i, active_word in enumerate(chunk):
            start_sec = active_word["start"]

            # Box stays until the exact start of the next word to prevent 1-frame gaps
            if i < len(chunk) - 1:
                end_sec = chunk[i + 1]["start"]
            else:
                end_sec = min(active_word["end"] + 0.1, next_chunk_start)

            start_time = format_time(start_sec)
            end_time = format_time(end_sec)

            w_w = word_widths[i]

            # Mathematical positioning relative to text baseline (center_y)
            # We want inner height 100px to perfectly balance padding.
            # Inner drawing goes from 0 to 100.
            drawing = f"{{\\p1}}m 0 0 l {w_w} 0 l {w_w} 100 l 0 100{{\\p0}}"

            # Outline=15 expands bounding box left by 15 and top by 15.
            # We shift pos_x left by 15 to balance the 30px total extra width.
            # We shift pos_y up by 96 to balance top/bottom padding against typical ink bounds.
            pos_x = current_x
            pos_y = center_y - 100

            pos_tag = f"{{\\an7\\pos({pos_x},{pos_y})}}"

            events.append(
                f"Dialogue: 0,{start_time},{end_time},ActiveBox,,0,0,0,,{pos_tag}{drawing}"
            )

            current_x += w_w + space_width

    os.makedirs(os.path.dirname(output_ass_path) or ".", exist_ok=True)
    with open(output_ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header + "\n".join(events) + "\n")

    print(f"Subtitles generated successfully at {output_ass_path}")
