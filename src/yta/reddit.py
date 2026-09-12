import os
import praw


# Get a AITA post from Reddit
def get_story(
    post_id: str | None = None, subreddit_name: str = "AmItheAsshole"
) -> tuple[str, str] | None:
    reddit = praw.Reddit(
        client_id=os.getenv("PRAW_CLIENT_ID", ""),
        client_secret=os.getenv("PRAW_SECRET", ""),
        user_agent=f"script:context:v1.0 (by /u/{os.getenv('PRAW_USERNAME', '')})",
    )

    if post_id:
        submission = reddit.submission(id=post_id)
        print(f"Fetching specific post ID: {post_id}")
        print(f"Title: {submission.title}")
        print(f"Score: {submission.score}")
        print(f"URL: {submission.url}")
        print(f"Selftext: {submission.selftext[:100]}...")
        print("-" * 40)
        return submission.title, submission.selftext

    # Select target subreddit
    subreddit = reddit.subreddit(subreddit_name)

    # Get top 1 posts from today
    for submission in subreddit.top(time_filter="day", limit=1):
        print(f"Title: {submission.title}")
        print(f"Score: {submission.score}")
        print(f"URL: {submission.url}")
        print(f"Selftext: {submission.selftext[:100]}...")
        print("-" * 40)

        return submission.title, submission.selftext

    return None
