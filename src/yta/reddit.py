import os
import praw


# Get a AITA post from Reddit
def get_story():
    reddit = praw.Reddit(
        client_id=os.getenv("PRAW_CLIENT_ID"),
        client_secret=os.getenv("PRAW_SECRET"),
        user_agent=f"script:context:v1.0 (by /u/{os.getenv('PRAW_USERNAME')})",
    )

    # Select target subreddit
    subreddit = reddit.subreddit("AmItheAsshole")

    # Get top 1 posts from today
    for submission in subreddit.top(time_filter="day", limit=1):
        print(f"Title: {submission.title}")
        print(f"Score: {submission.score}")
        print(f"URL: {submission.url}")
        print(f"Selftext: {submission.selftext}")

        return submission.title, submission.selftext
