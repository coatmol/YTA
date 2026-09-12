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
    args = parser.parse_args()

    if not args.video:
        parser.print_help()
        return

    story = reddit.get_story()
    if story is None:
        print("No story found.")
        return

    title, body = story
    formatted_script, gender = inference.format_script_for_shorts(title, body)

    print(f"[{gender.upper()}] {formatted_script}")
    print("\nGenerating Voiceover...")

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
