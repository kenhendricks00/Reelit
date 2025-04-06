from flask import Flask, jsonify, request, render_template, send_from_directory
import threading
import os
import sys
import time
import queue
import re

# Add the src directory to the Python path to allow importing main
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from main import run_pipeline, SUBREDDIT as DEFAULT_SUBREDDIT
except ImportError as e:
    print(f"Error importing main: {e}. Make sure main.py is in the same directory ({src_dir}) and all dependencies are installed.")
    # Define dummy functions/variables if import fails, so Flask can still load
    def run_pipeline():
        print("ERROR: run_pipeline could not be imported.")
    DEFAULT_SUBREDDIT = "ImportError"

app = Flask(__name__, template_folder='templates', static_folder='static')

# Global variables for tracking video generation
GENERATION_IN_PROGRESS = False
GENERATION_THREAD = None
RESULT_FILE = None
GENERATION_ERROR = None

# Progress tracking
PROGRESS_LOGS = []
CURRENT_STEP = "Initializing"
PROGRESS_PERCENTAGE = 0
PROGRESS_QUEUE = queue.Queue()  # For thread-safe communication

# Define main pipeline steps and their percentage weights
PIPELINE_STEPS = {
    "fetch_story": {"name": "Fetching Story", "weight": 10, "regex": r"Fetching.*story"},
    "generate_audio": {"name": "Generating Audio", "weight": 20, "regex": r"Generating narration audio"},
    "word_timestamps": {"name": "Processing Words", "weight": 20, "regex": r"Getting word timestamps"},
    "create_video": {"name": "Rendering Video", "weight": 50, "regex": r"Creating video"}
}

# Background videos mapping
BACKGROUND_VIDEOS = {
    "minecraft": "src/assets/background_minecraft.webm",
    "gta": "src/assets/background_gta.webm",
    "subway_surfer": "src/assets/background_subway_surfer.webm"
}

BACKGROUND_MUSIC_PATH = "src/assets/background_music.mp3"

class ProgressLogHandler:
    """Custom handler to capture log messages and update progress"""
    
    def __init__(self):
        self.progress_queue = PROGRESS_QUEUE
        self.rendering_started = False
        self.current_caption = None
    
    def write(self, message):
        """Process log messages and update progress"""
        if message.strip():
            # Add message to logs
            self.progress_queue.put(("log", message.strip()))
            
            # Update progress based on message content
            for step_id, step_info in PIPELINE_STEPS.items():
                if re.search(step_info["regex"], message, re.IGNORECASE):
                    # Found matching step, update current step and progress
                    self.progress_queue.put(("step", step_id))
                    if step_id == "create_video":
                        self.rendering_started = True
                    break
            
            # Track specific processing steps to provide detailed status
            if "Creating caption: '" in message:
                # Extract the caption text being processed
                try:
                    caption_text = message.split("Creating caption: '")[1].split("'")[0]
                    self.current_caption = caption_text
                    # Add special log entry for UI to pick up
                    self.progress_queue.put(("log", f"Processing caption: '{caption_text}'"))
                except:
                    pass
                    
            # Track specific video rendering progress indicators
            if self.rendering_started:
                # Track specific components of video rendering
                if "Narration audio loaded" in message:
                    self.progress_queue.put(("progress", 55))
                elif "title card configured" in message:
                    self.progress_queue.put(("progress", 60))
                elif "Generating subtitle images" in message:
                    self.progress_queue.put(("progress", 65))
                elif "Creating caption" in message:
                    self.progress_queue.put(("progress", 70))
                elif "Compositing final video" in message:
                    self.progress_queue.put(("progress", 75))
                elif "Video layers composited" in message:
                    self.progress_queue.put(("progress", 80))
                elif "Writing final video" in message:
                    self.progress_queue.put(("progress", 85))
                elif "Video created successfully" in message:
                    self.progress_queue.put(("progress", 95))
            
            # Check for sub-steps that indicate progress within a main step
            if "successfully" in message.lower() or "saved to" in message.lower():
                self.progress_queue.put(("progress_update", None))

def pipeline_wrapper(subreddit, background_video, music_volume=0.15):
    """Wrapper function to run the pipeline and manage the global flag."""
    global GENERATION_IN_PROGRESS, RESULT_FILE, GENERATION_ERROR, PROGRESS_LOGS, CURRENT_STEP, PROGRESS_PERCENTAGE
    
    RESULT_FILE = None
    GENERATION_ERROR = None
    PROGRESS_LOGS = ["Starting video generation pipeline..."]
    CURRENT_STEP = "Initializing"
    PROGRESS_PERCENTAGE = 0
    
    # Create a log handler to capture output for progress tracking
    log_handler = ProgressLogHandler()
    
    print(f"Background thread started for video generation with params: subreddit={subreddit}, background_video={background_video}, music_volume={music_volume}")
    
    # Add initial log entry
    PROGRESS_QUEUE.put(("log", f"Preparing to fetch story from r/{subreddit}"))
    PROGRESS_QUEUE.put(("log", f"Selected background: {os.path.basename(background_video)}"))
    PROGRESS_QUEUE.put(("log", f"Music volume set to: {int(music_volume * 100)}%"))
    
    try:
        # Redirect stdout to capture logs (save original)
        original_stdout = sys.stdout
        sys.stdout = log_handler
        
        # Call run_pipeline with the parameters
        result_file = run_pipeline(
            subreddit=subreddit,
            background_video_path=background_video,
            background_music_path=BACKGROUND_MUSIC_PATH,
            music_volume=music_volume
        )
        
        # Restore stdout
        sys.stdout = original_stdout
        
        if result_file and os.path.exists(result_file):
            RESULT_FILE = os.path.basename(result_file)
            print(f"Video generation completed successfully: {RESULT_FILE}")
            PROGRESS_QUEUE.put(("log", f"Video generation completed successfully: {RESULT_FILE}"))
            PROGRESS_QUEUE.put(("progress", 100))  # Set to 100% when complete
        else:
            GENERATION_ERROR = "Generation completed but no result file was produced."
            PROGRESS_QUEUE.put(("log", GENERATION_ERROR))
    except Exception as e:
        # Restore stdout in case of exception
        if sys.stdout != original_stdout:
            sys.stdout = original_stdout
            
        GENERATION_ERROR = str(e)
        print(f"Exception in background pipeline thread: {e}")
        PROGRESS_QUEUE.put(("log", f"Error: {GENERATION_ERROR}"))
    finally:
        GENERATION_IN_PROGRESS = False
        print("Background thread finished.")
        PROGRESS_QUEUE.put(("log", "Background thread finished."))

def process_progress_queue():
    """Process any pending messages in the progress queue"""
    global PROGRESS_LOGS, CURRENT_STEP, PROGRESS_PERCENTAGE
    
    try:
        while not PROGRESS_QUEUE.empty():
            message_type, message = PROGRESS_QUEUE.get_nowait()
            
            if message_type == "log":
                PROGRESS_LOGS.append(message)
                # Keep only the last 50 logs to avoid memory issues
                if len(PROGRESS_LOGS) > 50:
                    PROGRESS_LOGS = PROGRESS_LOGS[-50:]
            
            elif message_type == "step":
                step_id = message
                CURRENT_STEP = PIPELINE_STEPS[step_id]["name"]
                
                # Calculate progress percentage based on step weights
                current_step_index = list(PIPELINE_STEPS.keys()).index(step_id)
                completed_weight = sum(PIPELINE_STEPS[s]["weight"] for s in list(PIPELINE_STEPS.keys())[:current_step_index])
                PROGRESS_PERCENTAGE = completed_weight
            
            elif message_type == "progress_update":
                # Increment progress within current step
                current_step_id = next((s_id for s_id, s_info in PIPELINE_STEPS.items() if s_info["name"] == CURRENT_STEP), None)
                if current_step_id:
                    current_step_index = list(PIPELINE_STEPS.keys()).index(current_step_id)
                    completed_weight = sum(PIPELINE_STEPS[s]["weight"] for s in list(PIPELINE_STEPS.keys())[:current_step_index])
                    current_step_weight = PIPELINE_STEPS[current_step_id]["weight"]
                    
                    # Increment more significantly for each step
                    if current_step_id == "fetch_story":
                        # Increment by 50% of the current step weight
                        increment = current_step_weight * 0.5
                    elif current_step_id == "generate_audio":
                        # Increment by 33% of the current step weight
                        increment = current_step_weight * 0.33
                    elif current_step_id == "word_timestamps":
                        # Increment by 40% of the current step weight
                        increment = current_step_weight * 0.4
                    elif current_step_id == "create_video":
                        # Smaller increments for video creation as we track specific steps
                        increment = current_step_weight * 0.1
                    else:
                        # Default increment of 25%
                        increment = current_step_weight * 0.25
                    
                    PROGRESS_PERCENTAGE = min(completed_weight + increment, 95)
            
            elif message_type == "progress":
                PROGRESS_PERCENTAGE = message
    
    except Exception as e:
        print(f"Error processing progress queue: {e}")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_video_endpoint():
    """API endpoint to trigger the video generation pipeline."""
    global GENERATION_IN_PROGRESS, GENERATION_THREAD, RESULT_FILE, GENERATION_ERROR

    if GENERATION_IN_PROGRESS:
        # Check if the thread is still alive
        if GENERATION_THREAD and GENERATION_THREAD.is_alive():
            return jsonify({"status": "error", "message": "Video generation is already in progress."}), 429 # Too Many Requests
        else:
            # Thread finished unexpectedly or flag wasn't reset properly, allow starting a new one
            print("Warning: GENERATION_IN_PROGRESS was True, but thread is not alive. Resetting flag.")
            GENERATION_IN_PROGRESS = False

    # Get parameters from form data
    subreddit = request.form.get('subreddit', DEFAULT_SUBREDDIT)
    selected_game = request.form.get('selected_game')
    music_volume = float(request.form.get('music_volume', 0.15))  # Default to 15%

    # Validate game selection
    if not selected_game or selected_game not in BACKGROUND_VIDEOS:
        return jsonify({
            "status": "error", 
            "message": f"Invalid game selection: {selected_game}. Valid options are: {', '.join(BACKGROUND_VIDEOS.keys())}"
        }), 400

    # Get the background video path for the selected game
    background_video = BACKGROUND_VIDEOS[selected_game]
    
    # Reset result tracking
    RESULT_FILE = None
    GENERATION_ERROR = None
    
    print(f"Received request to generate video: subreddit={subreddit}, game={selected_game}, bg_video={background_video}, music_vol={music_volume}")
    GENERATION_IN_PROGRESS = True
    
    # Run the pipeline in a separate thread to avoid blocking the request
    GENERATION_THREAD = threading.Thread(
        target=pipeline_wrapper, 
        args=(subreddit, background_video, music_volume),
        daemon=True
    )
    GENERATION_THREAD.start()

    return jsonify({"status": "success", "message": "Video generation started in the background."}), 202 # Accepted

@app.route('/status', methods=['GET'])
def generation_status():
    """API endpoint to check the status of video generation."""
    global GENERATION_IN_PROGRESS, GENERATION_THREAD, RESULT_FILE, GENERATION_ERROR, PROGRESS_LOGS, CURRENT_STEP, PROGRESS_PERCENTAGE

    # Process any pending progress updates
    process_progress_queue()

    if GENERATION_IN_PROGRESS:
        if GENERATION_THREAD and GENERATION_THREAD.is_alive():
            status_message = "Video generation is currently in progress."
        else:
            # Should ideally not happen if flag is managed correctly
            status_message = "Status unclear: Flag indicates progress, but thread is not alive."
            GENERATION_IN_PROGRESS = False # Reset flag if thread died unexpectedly
    else:
        if RESULT_FILE:
            status_message = "Video generation completed successfully."
            PROGRESS_PERCENTAGE = 100
        elif GENERATION_ERROR:
            status_message = f"Video generation failed: {GENERATION_ERROR}"
        else:
            status_message = "No video generation in progress."

    return jsonify({
        "in_progress": GENERATION_IN_PROGRESS, 
        "message": status_message,
        "result_file": RESULT_FILE,
        "error": GENERATION_ERROR,
        "progress": {
            "percentage": PROGRESS_PERCENTAGE,
            "current_step": CURRENT_STEP,
            "logs": PROGRESS_LOGS[-10:]  # Return last 10 log entries
        }
    })

@app.route('/download/<filename>')
def download_file(filename):
    """Download the generated video file."""
    return send_from_directory(os.path.join(src_dir, 'output'), filename, as_attachment=True)

if __name__ == '__main__':
    # Check if required files/configs are present before starting
    print("Checking prerequisites...")
    # Check for background video files
    for game, path in BACKGROUND_VIDEOS.items():
        if not os.path.exists(path):
            print(f"Warning: Background video for {game} not found at '{path}'.")
    
    # Check for background music
    if not os.path.exists(BACKGROUND_MUSIC_PATH):
        print(f"Warning: Background music not found at '{BACKGROUND_MUSIC_PATH}'.")
    
    if not os.getenv("REDDIT_CLIENT_ID"):
        print("Warning: REDDIT_CLIENT_ID not found in environment variables or .env file. Reddit scraping will fail.")

    print("Starting Flask server...")
    # Use host='0.0.0.0' to make it accessible on the network
    # Disable the reloader to prevent conflicts with background task
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False) 