# YTA

A python tool for YouTube Automation (reddit AITA stories)

## Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- **FFmpeg** installed on your system and added to your system PATH
- A Reddit account and [Reddit API credentials](https://www.reddit.com/prefs/apps)
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

## Setup

1. **Clone the repository and install dependencies:**

   The project uses `uv` for lightning-fast dependency resolution and virtual environment management.

   ```sh
   uv sync
   ```

2. **Configure your environment variables:**

   Create a `.env` file in the root of the project with your Reddit and Gemini API credentials:

   ```env
   PRAW_CLIENT_ID=your_14_character_client_id
   PRAW_SECRET=your_27_character_client_secret
   PRAW_USERNAME=your_reddit_username
   GEMINI_API_KEY=your_gemini_api_key
   ```

   > **Note:** Ensure that `PRAW_CLIENT_ID` is set to the actual 14-character alphanumeric Client ID (found under your application name in the Reddit App Preferences), **not** the name of the application itself.

3. **Fonts:**

   Ensure you have the `impact.ttf` font installed on your system or placed in your project root, as it is used for rendering subtitles.

## Usage

You can run the script using `uv`. You must provide a background video (like Minecraft parkour or GTA V gameplay) to be cropped to a 9:16 aspect ratio. You can also optionally provide background music.

```sh
uv run src/main.py --video path/to/background_video.mp4 --bgm path/to/background_music.mp3
```

**How it works:**
1. Authenticates with Reddit and fetches the top post.
2. Uses **Gemini** to rewrite and optimize the Reddit post into a viral, high-retention 40-second script, automatically detecting the narrator's gender.
3. Uses **Edge TTS** to generate a natural-sounding AI voiceover.
4. Generates word-by-word **ASS subtitles** featuring dynamic highlights.
5. Uses **FFmpeg** to crop the video to 9:16, mix the audio, burn the subtitles, and output the final video to `output/final_short.mp4`.

## License

This project is open source.
