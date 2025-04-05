import os
import datetime
import random
import string
import re # Import regex module

from reddit_scraper import get_random_top_story
from tts_generator import create_narration
from video_creator import create_video
from alignment import get_word_timestamps # Import the new function

# --- Configuration ---
SUBREDDIT = "AmItheAsshole" # Or choose another like "confession", "tifu"
# --- Paths ---
BACKGROUND_VIDEO_PATH = "assets/background.mp4" # Path to background video
BACKGROUND_MUSIC_PATH = "assets/background_music.mp3" # Path to background music
OUTPUT_DIR = "output" # Directory for output files
ASSETS_DIR = "assets" # Directory for assets

# Ensure necessary directories exist
# Use the adjusted paths here too
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

def generate_random_filename(prefix="video", length=8):
    """Generates a random filename to avoid overwrites."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}_{timestamp}_{random_chars}"

def run_pipeline():
    """Runs the full pipeline: fetch story -> generate audio -> create video with title/captions."""
    print(f"--- Starting Video Generation Pipeline ---")

    # 1. Get Reddit Story
    print(f"\nStep 1: Fetching random story from r/{SUBREDDIT}...")
    try:
        title_text, story_text, post_url = get_random_top_story(SUBREDDIT) # Keep original title in title_text
        if not title_text or not story_text:
            print("Failed to retrieve a story title or text. Exiting.")
            return
        print(f"Successfully fetched story: '{title_text}'")
        # Post URL is fetched but not used in this version
        # print(f"Post URL: {post_url}") 
    except ValueError as e:
        print(f"Error fetching story: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during story fetching: {e}")
        return

    # Prepare text for narration - use original title and story
    narration_text = f"{title_text}. {story_text}" 
    # Basic cleaning
    narration_text = narration_text.replace("&", " and ").replace("#", " number ") 
    # Replace AITA variations for TTS
    narration_text = re.sub(r'\bAITA\b\??', 'Am I the asshole?', narration_text, flags=re.IGNORECASE)
    # Replace age/gender shorthand (e.g., 42m -> 42 male, 23F -> 23 female)
    # Use capture group () for the number \d+ and backreference \1
    narration_text = re.sub(r'\b(\d+)[mM]\b', r'\1 male', narration_text)
    narration_text = re.sub(r'\b(\d+)[fF]\b', r'\1 female', narration_text)
    print(f"  Text prepared for narration (AITA, Age/Gender replaced). Length: {len(narration_text)}")

    # Generate unique filenames for this run
    base_filename = generate_random_filename(prefix=SUBREDDIT)
    audio_filename = os.path.join(OUTPUT_DIR, f"{base_filename}_narration.mp3")
    video_filename = os.path.join(OUTPUT_DIR, f"{base_filename}_final.mp4")
    # screenshot_filename = os.path.join(OUTPUT_DIR, f"{base_filename}_screenshot.png") # Removed

    # --- Screenshot step removed --- 

    # 2. Generate Narration
    print(f"\nStep 2: Generating narration audio...")
    if not create_narration(narration_text, audio_filename):
        print("Failed to create narration. Exiting.")
        # ... (cleanup audio if exists) ...
        if os.path.exists(audio_filename):
            try: os.remove(audio_filename)
            except OSError as e: print(f"Error removing partial audio file {audio_filename}: {e}")
        return
    print(f"Narration saved to: {audio_filename}")

    # --- New Step: Get Word Timestamps --- 
    print(f"\nStep 2.5: Getting word timestamps using Whisper...")
    # Use a small model for faster processing, adjust if needed (e.g., "base.en")
    word_timestamps = get_word_timestamps(audio_filename, model_name="tiny.en") 
    if not word_timestamps:
        print("Failed to get word timestamps from audio. Cannot proceed with accurate caption sync. Exiting.")
        # Clean up audio file
        if os.path.exists(audio_filename): os.remove(audio_filename)
        return
    print(f"Successfully obtained {len(word_timestamps)} word timestamps.")
    # --- End New Step --- 

    # 3. Create Video (Pass background music path)
    print(f"\nStep 3: Creating video...")
    if not os.path.exists(BACKGROUND_VIDEO_PATH):
         print(f"Error: Background video not found at '{BACKGROUND_VIDEO_PATH}'. Please add it.")
         # Clean up audio file
         if os.path.exists(audio_filename): os.remove(audio_filename)
         return
    # Check for background music file existence (optional but good practice)
    if not os.path.exists(BACKGROUND_MUSIC_PATH):
        print(f"Warning: Background music file not found at '{BACKGROUND_MUSIC_PATH}'. Proceeding without music.")
        # Set path to None so create_video knows to skip it
        music_path_to_pass = None 
    else:
        music_path_to_pass = BACKGROUND_MUSIC_PATH

    # Pass music_path_to_pass to create_video
    if not create_video(audio_filename, BACKGROUND_VIDEO_PATH, title_text, story_text, word_timestamps, music_path_to_pass, video_filename):
        print("Failed to create video. Exiting.")
        # Clean up audio file
        if os.path.exists(audio_filename): os.remove(audio_filename)
        return
    print(f"Final video saved to: {video_filename}")

    # 4. Cleanup (Optional: remove intermediate audio file)
    cleanup_intermediate_files = True
    if cleanup_intermediate_files:
        print(f"\nStep 4: Cleaning up intermediate audio file...")
        if os.path.exists(audio_filename):
            try:
                os.remove(audio_filename)
                print(f"Removed intermediate audio file: {audio_filename}")
            except OSError as e:
                print(f"Error removing intermediate audio file {audio_filename}: {e}")
        # No screenshot to cleanup anymore

    print(f"\n--- Pipeline Finished Successfully ---")

if __name__ == "__main__":
    run_pipeline() 