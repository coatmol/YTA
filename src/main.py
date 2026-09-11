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
    formatted_script = inference.format_script_for_shorts(title, body)

    print(formatted_script)
    print("\nGenerating Voiceover...")
    tts.create_tts(formatted_script)


if __name__ == "__main__":
    main()
