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

    formatted_script, gender, yt_title, yt_desc = inference.format_script_for_shorts(
        title, body, target_words=args.words
    )

    print(f"[{gender.upper()}] {formatted_script}")
    print("\n--- YouTube Metadata ---")
    print(f"Title: {yt_title}")
    print(f"Description:\n{yt_desc}")
    print("------------------------\n")
    
    with open("output/metadata.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {yt_title}\n\nDescription:\n{yt_desc}\n")

    print("Generating Voiceover...")

    voice = "en-US-JennyNeural" if gender == "female" else "en-US-AndrewNeural"
    tts.create_tts(formatted_script, voice=voice)

    print("\nGenerating Subtitles...")
    sub_path = "output/subtitles.ass"
    subtitles.generate_ass(tts.JSON_OUTPUT, sub_path)

    if args.video:
        print("\nProcessing Video...")
        video.create_short_video(
            input_video_path=args.video,
            audio_path=tts.AUDIO_OUTPUT,
            bgm_path=args.bgm,
            subtitles_path=sub_path,
            output_path="output/final_short.mp4",
        )


if __name__ == "__main__":
    main()
