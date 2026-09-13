import dotenv
import warnings
import logging
import argparse

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)

dotenv.load_dotenv()
from yta import *


def main():
    parser = argparse.ArgumentParser(
        description="YTA - Youtube Shorts Text-to-Video Automation"
    )
    parser.add_argument(
        "--video", "-v", type=str, help="Path to input background video (MP4)"
    )
    parser.add_argument(
        "--bgm", "-b", type=str, help="Path to background music audio (MP3/WAV)"
    )
    parser.add_argument(
        "--post",
        "-p",
        type=str,
        help="Specific Reddit post ID to fetch (skips daily top search)",
    )
    parser.add_argument(
        "--subreddit",
        "-r",
        type=str,
        help="Specific Reddit subreddit to fetch posts from",
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        help="Specific text file to use for the video instead of fetching from Reddit (First line is title, rest is body)",
    )
    parser.add_argument(
        "--words",
        "-w",
        type=int,
        default=200,
        help="Target word count for the video script (default: 200)",
    )
    parser.add_argument(
        "--sfx",
        action="store_true",
        help="Enable sound effects (reads from assets/sound)",
    )
    args = parser.parse_args()

    if not args.video:
        parser.print_help()
        return

    if args.text:
        with open(args.text, "r", encoding="utf-8") as f:
            title = f.readline().strip()
            body = f.read().strip()
    else:
        story = reddit.get_story(post_id=args.post, subreddit_name=args.subreddit)
        if story is None:
            print("No story found.")
            return

        title, body = story

    available_sfx = None
    if args.sfx:
        available_sfx = sfx.get_available_sfx("assets/sound")
        if available_sfx:
            print(f"Detected {len(available_sfx)} available sound effects.")
        else:
            print("SFX enabled but no sound effects found in assets/sound.")

    formatted_script_raw, gender, yt_title, yt_desc = inference.format_script_for_shorts(
        title, body, target_words=args.words, use_sfx=args.sfx, available_sfx=available_sfx
    )

    clean_script, sfx_events_raw = sfx.parse_script_for_sfx(formatted_script_raw)

    print(f"[{gender.upper()}] {clean_script}")
    if sfx_events_raw:
        print(f"\n[SFX Detected]: {', '.join([e['name'] for e in sfx_events_raw])}")

    print("\n--- YouTube Metadata ---")
    print(f"Title: {yt_title}")
    print(f"Description:\n{yt_desc}")
    print("------------------------\n")
    
    with open("output/metadata.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {yt_title}\n\nDescription:\n{yt_desc}\n")

    print("Generating Voiceover...")

    voice = "en-US-JennyNeural" if gender == "female" else "en-US-AndrewNeural"
    tts.create_tts(clean_script, voice=voice)

    print("\nGenerating Subtitles...")
    sub_path = "output/subtitles.ass"
    subtitles.generate_ass(tts.JSON_OUTPUT, sub_path)

    if args.video:
        resolved_sfx = sfx.resolve_sfx_timestamps(sfx_events_raw, tts.JSON_OUTPUT)
        if resolved_sfx:
            print(f"Found {len(resolved_sfx)} sound effects to mix in.")
            
        print("\nProcessing Video...")
        video.create_short_video(
            input_video_path=args.video,
            audio_path=tts.AUDIO_OUTPUT,
            bgm_path=args.bgm,
            subtitles_path=sub_path,
            sfx_events=resolved_sfx,
            output_path="output/final_short.mp4",
        )


if __name__ == "__main__":
    main()
