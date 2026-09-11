import dotenv
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)

dotenv.load_dotenv()
from yta import *


def main():
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


if __name__ == "__main__":
    main()
