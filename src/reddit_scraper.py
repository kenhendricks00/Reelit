import praw
import os
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv()

def get_reddit_instance():
    """Initializes and returns a PRAW Reddit instance."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        raise ValueError("Reddit API credentials not found in .env file. "
                         "Please ensure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, "
                         "and REDDIT_USER_AGENT are set.")

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    print("PRAW instance created successfully.")
    return reddit

def get_random_top_story(subreddit_name="AmItheAsshole", limit=25):
    """Fetches top stories from a subreddit and returns a random one."""
    reddit = get_reddit_instance()
    try:
        subreddit = reddit.subreddit(subreddit_name)
        # Fetch top posts (e.g., from the last day, week, or all time - 'day', 'week', 'month', 'year', 'all')
        # Using 'hot' might be better for fresher content than 'top' with a time limit
        hot_posts = list(subreddit.hot(limit=limit))

        if not hot_posts:
            print(f"No hot posts found in r/{subreddit_name} with limit {limit}.")
            return None, None, None

        # Filter out potential mod posts or posts without substantial text
        valid_posts = [
            post for post in hot_posts
            if not post.stickied and post.selftext.strip() # Ensure it has body text
        ]

        if not valid_posts:
             print(f"No suitable non-stickied posts with text found in the top {limit} hot posts of r/{subreddit_name}.")
             return None, None, None

        # Select a random post
        random_post = random.choice(valid_posts)

        # Construct the full URL (permalink)
        post_url = f"https://www.reddit.com{random_post.permalink}"

        print(f"Selected post: '{random_post.title}' from r/{subreddit_name}")
        # Return title, text, and URL
        return random_post.title, random_post.selftext, post_url

    except Exception as e:
        print(f"An error occurred while fetching from Reddit: {e}")
        # Return None for all three values
        return None, None, None

if __name__ == '__main__':
    # Example usage:
    try:
        # Update example usage to expect three values
        title, story, url = get_random_top_story("AmItheAsshole")
        if title and story and url:
            print("\n--- Story ---")
            print(f"Title: {title}")
            print(f"URL: {url}")
            print(f"Story: {story[:200]}...") # Print first 200 chars for brevity
        else:
            print("Could not retrieve a story.")
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 