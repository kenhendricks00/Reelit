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
BACKGROUND_VIDEO_PATH = "src/assets/background_minecraft.webm" # Default background video
BACKGROUND_MUSIC_PATH = "src/assets/background_music.mp3" # Path to background music
OUTPUT_DIR = "src/output" # Directory for output files
ASSETS_DIR = "src/assets" # Directory for assets

# Ensure necessary directories exist
# Use the adjusted paths here too
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

def generate_random_filename(prefix="video", length=8):
    """Generates a random filename to avoid overwrites."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}_{timestamp}_{random_chars}"

def run_pipeline(subreddit=SUBREDDIT, background_video_path=BACKGROUND_VIDEO_PATH, 
                background_music_path=BACKGROUND_MUSIC_PATH, music_volume=0.15):
    """Runs the full pipeline: fetch story -> generate audio -> create video with title/captions.
    
    Args:
        subreddit (str): Subreddit to fetch stories from
        background_video_path (str): Path to the background video file
        background_music_path (str): Path to the background music file
        music_volume (float): Volume of background music (0.0 to 1.0)
        
    Returns:
        str: Path to the generated video file, or None if failed
    """
    print(f"--- Starting Video Generation Pipeline ---")
    print(f"Parameters: subreddit={subreddit}, bg_video={background_video_path}, music_vol={music_volume}")

    # 1. Get Reddit Story
    print(f"\nStep 1: Fetching random story from r/{subreddit}...")
    try:
        title_text, story_text, post_url = get_random_top_story(subreddit) # Keep original title in title_text
        if not title_text or not story_text:
            print("Failed to retrieve a story title or text. Exiting.")
            return None
        print(f"Successfully fetched story: '{title_text}'")
        # Post URL is fetched but not used in this version
        # print(f"Post URL: {post_url}") 
    except ValueError as e:
        print(f"Error fetching story: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during story fetching: {e}")
        return None

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
    base_filename = generate_random_filename(prefix=subreddit)
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
        return None
    print(f"Narration saved to: {audio_filename}")

    # --- New Step: Get Word Timestamps --- 
    print(f"\nStep 2.5: Getting word timestamps using Whisper...")
    # Use a small model for faster processing, adjust if needed (e.g., "base.en")
    word_timestamps = get_word_timestamps(audio_filename, model_name="tiny.en") 
    if not word_timestamps:
        print("Failed to get word timestamps from audio. Cannot proceed with accurate caption sync. Exiting.")
        # Clean up audio file
        if os.path.exists(audio_filename): os.remove(audio_filename)
        return None
    print(f"Successfully obtained {len(word_timestamps)} word timestamps.")
    # --- End New Step --- 

    # 3. Create Video (Pass background music path and volume)
    print(f"\nStep 3: Creating video...")
    if not os.path.exists(background_video_path):
         print(f"Error: Background video not found at '{background_video_path}'. Please add it.")
         # Clean up audio file
         if os.path.exists(audio_filename): os.remove(audio_filename)
         return None
    # Check for background music file existence
    if not os.path.exists(background_music_path):
        print(f"Warning: Background music file not found at '{background_music_path}'. Proceeding without music.")
        # Set path to None so create_video knows to skip it
        music_path_to_pass = None 
    else:
        music_path_to_pass = background_music_path

    # Pass music_path_to_pass and music_volume to create_video
    if not create_video(audio_filename, background_video_path, title_text, story_text, 
                        word_timestamps, music_path_to_pass, video_filename, music_volume):
        print("Failed to create video. Exiting.")
        # Clean up audio file
        if os.path.exists(audio_filename): os.remove(audio_filename)
        return None
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
    return video_filename

if __name__ == "__main__":
    run_pipeline() 