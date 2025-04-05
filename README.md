# Reelit - Reddit Story Video Generator

Automate the creation of short-form videos (TikTok, YouTube Shorts, Instagram Reels) by combining narrated Reddit stories with background footage and synchronized captions.

## Features

- **Multi-Platform Compatibility**: Outputs 9:16 vertical videos.
- **Reddit Integration**: Scrapes stories using PRAW.
- **AI Narration**: Converts text (with 'AITA' and age/gender substitutions) to speech using gTTS.
- **Accurate Captions**: Uses OpenAI Whisper to generate word-level timestamps for precise caption synchronization.
- **Dynamic Title Card**: Draws the post title onto a provided template image.
- **Layered Audio**: Mixes narration with background music.
- **Automated Video Creation**: Combines background video, dynamic title card, narration, music, and timed captions using MoviePy.
- **Simple API**: Uses Flask for triggering video generation via a POST request.

## How It Works

1.  **Trigger**: A POST request to the `/generate` endpoint (via Flask) starts the process.
2.  **Story Selection**: Fetches a random, popular story (title & body) from a chosen subreddit (e.g., r/AmItheAsshole) using PRAW.
3.  **Narration Generation**:
    - Performs text substitutions (e.g., 'AITA' -> 'Am I the asshole?', '42m' -> '42 male').
    - Converts the modified text to an MP3 audio narration using gTTS.
4.  **Timestamp Generation**:
    - Uses OpenAI Whisper to transcribe the generated MP3 narration and extracts precise start/end times for each spoken word.
5.  **Title Card Creation**:
    - Loads your `title_template.png` from the `assets` folder.
    - Uses Pillow to dynamically draw the original Reddit post title onto the template, adjusting font size for fit. Saves this as a temporary image.
6.  **Caption Image Generation**:
    - Iterates through the word timestamps obtained from Whisper.
    - Groups words into small chunks (e.g., 2 words or breaking on pauses).
    - For each chunk, uses Pillow to create a transparent PNG image with the caption text (white, bold font with black outline).
7.  **Video Assembly**:
    - Loads the background video (`background.mp4`) and background music (`background_music.mp3`) from `assets`.
    - Loops/trims background video and music to match narration length.
    - Reduces background music volume.
    - Combines narration and background music into a composite audio track.
    - Uses MoviePy to composite:
      - The background video (cropped to 9:16).
      - The dynamically generated title card (shown for the estimated duration of the spoken title).
      - The sequence of generated caption images, timed precisely using Whisper timestamps.
    - Sets the composite audio track to the final video.
8.  **Output**: Saves the final MP4 video to the `output/` directory.

## Technologies Behind the Magic

- **Python**: The core language.
  - **PRAW**: Reddit API integration.
  - **gTTS**: Text-to-Speech generation.
  - **openai-whisper**: Audio transcription and word-level timestamp generation.
  - **Pillow (PIL Fork)**: Image manipulation (drawing title on template, creating caption images).
  - **MoviePy**: Video and audio editing/compositing.
  - **Flask**: Simple web API.
  - **python-dotenv**: Environment variable management for API keys.
- **FFmpeg**: Essential backend for MoviePy and Whisper (must be installed separately).

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Create & Activate Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows: .\venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```
3.  **Install FFmpeg:**
    - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
    - Ensure the `ffmpeg` executable is in your system's PATH.
4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    # Note: Whisper installation might take time as it includes PyTorch.
    ```
5.  **Set up Reddit API Credentials:**
    - Create a `.env` file in the root directory.
    - Add your credentials:
    ```dotenv
    REDDIT_CLIENT_ID='your_client_id'
    REDDIT_CLIENT_SECRET='your_client_secret'
    REDDIT_USER_AGENT='your_user_agent'
    ```
6.  **Prepare Assets:**
    - Ensure the following files are inside the `assets/` directory:
      - `background.mp4` (Your background video)
      - `background_music.mp3` (Your background music)
      - `title_template.png` (Your title card template)
      - `Inter-Bold.ttf` (Or your desired font file - **update font path in `src/video_creator.py` if different**)

## Usage

1.  **Start the Server:**
    - Navigate to the `src` directory: `cd src`
    - Run the Flask app: `python app.py`
    - Keep this terminal running.
2.  **Trigger Generation:**
    - Open a **new** terminal.
    - Send a POST request: `curl -X POST http://127.0.0.1:5000/generate`
3.  **Monitor & Retrieve:**
    - Watch the logs in the first terminal.
    - The first run will download the Whisper model (`tiny.en` by default).
    - The process (especially Whisper transcription) can take some time.
    - Find the final video in the `output/` directory.

## Customization

- **Subreddit:** Change `SUBREDDIT` variable in `src/main.py`.
- **Title Card Text:** Adjust font size range, color, boundary box in `draw_title_on_template` within `src/video_creator.py`.
- **Caption Style:** Modify font, size, colors, outline in `create_subtitle_image` within `src/video_creator.py`.
- **Caption Grouping:** Adjust `MAX_WORDS_PER_CAPTION` or `MIN_GAP_BETWEEN_CAPTIONS` in `create_video`.
- **Music Volume:** Change `music_volume` default in `create_video`.
- **Whisper Model:** Modify `model_name` in `get_word_timestamps` call within `src/main.py` (e.g., to "base.en" for potentially better accuracy but slower speed).
