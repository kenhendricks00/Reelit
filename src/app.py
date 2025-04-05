from flask import Flask, jsonify, request
import threading
import os
import sys
import time

# Add the src directory to the Python path to allow importing main
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from main import run_pipeline, SUBREDDIT as DEFAULT_SUBREDDIT, BACKGROUND_VIDEO_PATH as DEFAULT_BG_VIDEO
except ImportError as e:
    print(f"Error importing main: {e}. Make sure main.py is in the same directory ({src_dir}) and all dependencies are installed.")
    # Define dummy functions/variables if import fails, so Flask can still load
    def run_pipeline():
        print("ERROR: run_pipeline could not be imported.")
    DEFAULT_SUBREDDIT = "ImportError"
    DEFAULT_BG_VIDEO = "ImportError"

app = Flask(__name__)

# Global variable to track if a generation task is running
GENERATION_IN_PROGRESS = False
GENERATION_THREAD = None

def pipeline_wrapper():
    """Wrapper function to run the pipeline and manage the global flag."""
    global GENERATION_IN_PROGRESS
    print("Background thread started for video generation.")
    try:
        run_pipeline() # This function now prints its own progress
    except Exception as e:
        print(f"Exception in background pipeline thread: {e}")
    finally:
        GENERATION_IN_PROGRESS = False
        print("Background thread finished.")

@app.route('/generate', methods=['POST'])
def generate_video_endpoint():
    """API endpoint to trigger the video generation pipeline."""
    global GENERATION_IN_PROGRESS, GENERATION_THREAD

    if GENERATION_IN_PROGRESS:
        # Check if the thread is still alive
        if GENERATION_THREAD and GENERATION_THREAD.is_alive():
             return jsonify({"status": "error", "message": "Video generation is already in progress."}), 429 # Too Many Requests
        else:
            # Thread finished unexpectedly or flag wasn't reset properly, allow starting a new one
            print("Warning: GENERATION_IN_PROGRESS was True, but thread is not alive. Resetting flag.")
            GENERATION_IN_PROGRESS = False

    # Optional: Allow specifying subreddit and background video via POST request JSON body
    # data = request.get_json()
    # subreddit = data.get('subreddit', DEFAULT_SUBREDDIT) if data else DEFAULT_SUBREDDIT
    # background_video = data.get('background_video', DEFAULT_BG_VIDEO) if data else DEFAULT_BG_VIDEO
    # TODO: Pass these parameters to run_pipeline if implemented there

    print("Received request to generate video.")
    GENERATION_IN_PROGRESS = True
    # Run the pipeline in a separate thread to avoid blocking the request
    GENERATION_THREAD = threading.Thread(target=pipeline_wrapper, daemon=True)
    GENERATION_THREAD.start()

    return jsonify({"status": "success", "message": "Video generation started in the background."}), 202 # Accepted

@app.route('/status', methods=['GET'])
def generation_status():
    """API endpoint to check the status of video generation."""
    global GENERATION_IN_PROGRESS, GENERATION_THREAD

    if GENERATION_IN_PROGRESS:
        if GENERATION_THREAD and GENERATION_THREAD.is_alive():
            status_message = "Video generation is currently in progress."
        else:
             # Should ideally not happen if flag is managed correctly
             status_message = "Status unclear: Flag indicates progress, but thread is not alive."
             GENERATION_IN_PROGRESS = False # Reset flag if thread died unexpectedly
    else:
        status_message = "No video generation in progress."

    return jsonify({"in_progress": GENERATION_IN_PROGRESS, "message": status_message})

if __name__ == '__main__':
    # Check if required files/configs are present before starting
    print("Checking prerequisites...")
    if DEFAULT_SUBREDDIT == "ImportError":
        print("Critical Error: Could not import configuration from main.py. Flask app cannot run.")
    elif not os.path.exists(DEFAULT_BG_VIDEO):
        print(f"Warning: Default background video '{DEFAULT_BG_VIDEO}' not found. The /generate endpoint will fail unless a valid path is provided or the default path is fixed.")
    if not os.getenv("REDDIT_CLIENT_ID"):
         print("Warning: REDDIT_CLIENT_ID not found in environment variables or .env file. Reddit scraping will fail.")

    print("Starting Flask server...")
    # Use host='0.0.0.0' to make it accessible on the network
    # Disable the reloader to prevent conflicts with Playwright background task
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False) 