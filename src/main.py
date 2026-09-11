from yta import *
import dotenv


def main():
    print("Hello, World!")
    dotenv.load_dotenv()

    reddit.get_aita()


if __name__ == "__main__":
    main()
