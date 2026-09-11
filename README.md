# YTA

A python tool for YouTube Automation (reddit AITA stories)

## Prerequisites

- Python 3.13 or newer
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- A Reddit account and [Reddit API credentials](https://www.reddit.com/prefs/apps)

## Setup

1. **Clone the repository and install dependencies:**

   The project uses `uv` for lightning-fast dependency resolution and virtual environment management.

   ```sh
   uv sync
   ```

2. **Configure your environment variables:**

   Create a `.env` file in the root of the project with your Reddit API credentials:

   ```env
   PRAW_CLIENT_ID=your_14_character_client_id
   PRAW_SECRET=your_27_character_client_secret
   PRAW_USERNAME=your_reddit_username
   ```

   > **Note:** Ensure that `PRAW_CLIENT_ID` is set to the actual 14-character alphanumeric Client ID (found under your application name in the Reddit App Preferences), **not** the name of the application itself.

## Usage

You can run the script using `uv`:

```sh
uv run src/main.py
```

This will authenticate with Reddit, fetch the top 5 posts from the target subreddit from the past day, and output their:

- Title
- Score
- URL
- A snippet of the post content
- The top comment on the post

## License

This project is open source.
