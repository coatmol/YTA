import dotenv
dotenv.load_dotenv()

from yta import *


def main():
    print("Hello, World!")

    story = reddit.get_story()
    if story is None:
        print("No story found.")
        return

    title, body = story
    formatted_script = inference.format_script_for_shorts(title, body)

    print(formatted_script)


if __name__ == "__main__":
    main()
