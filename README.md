# Reelit - Reddit Story Video Generator

Automate the creation of short-form videos (TikTok, YouTube Shorts, Instagram Reels) by combining narrated Reddit stories with background footage and synchronized captions, all through a simple web interface.

## Features

- **Web UI**: Easy-to-use interface built with Flask and Tailwind CSS for selecting subreddits, background videos, and initiating generation.
- **Multi-Platform Compatibility**: Outputs 9:16 vertical videos.
- **Reddit Integration**: Scrapes stories using PRAW.
- **AI Narration**: Converts text (with 'AITA' and age/gender substitutions) to speech using gTTS.
- **Accurate Captions**: Uses OpenAI Whisper to generate word-level timestamps for precise caption synchronization.
- **Dynamic Title Card**: Draws the post title onto a provided template image, adapting font size.
- **Background Options**: Choose from multiple background videos (Minecraft, GTA, Subway Surfer).
- **Layered Audio**: Mixes narration with adjustable background music volume.
- **Automated Video Creation**: Combines background video, title card, narration, music, and timed captions using MoviePy.
- **Real-time Progress**: Monitor the generation process with a detailed progress bar and logs in the web UI.
- **Direct Download & Replay**: Download the generated video or watch it directly in the browser on completion.
- **Git LFS**: Handles large background video files efficiently.

## How It Works

1.  **Frontend Interaction**: User selects subreddit, background video, and music volume via the web interface served by Flask.
2.  **Trigger**: Submitting the form sends a POST request to the `/generate` endpoint.
3.  **Backend Pipeline (run_pipeline in main.py)**:
    a. **Story Selection**: Fetches a random, popular story from the chosen subreddit.
    b. **Narration Generation**: Cleans text (substitutions) and generates MP3 audio using gTTS.
    c. **Timestamp Generation**: Uses Whisper to get word timestamps from the narration.
    d. **Title Card Creation**: Dynamically draws the title on `title_template.png`.
    e. **Caption Image Generation**: Creates transparent PNGs for caption chunks based on timestamps.
    f. **Video Assembly (create_video in video_creator.py)**: Combines chosen background video (via Git LFS), music, title card, and captions using MoviePy.
4.  **Progress Tracking**: The Flask app captures logs and updates progress status via a queue.
5.  **Frontend Polling**: The web UI periodically polls the `/status` endpoint to update the progress bar, logs, and current step.
6.  **Result Display**: Upon completion, the UI shows a success message, an embedded video player, and download/retry buttons.

## Technologies Behind the Magic

- **Python**: Core backend language.
  - **Flask**: Web framework and API.
  - **PRAW**: Reddit API integration.
  - **gTTS**: Text-to-Speech generation.
  - **openai-whisper**: Audio transcription and word-level timestamp generation.
  - **Pillow (PIL Fork)**: Image manipulation (drawing title, creating captions).
  - **MoviePy**: Video and audio editing/compositing.
  - **python-dotenv**: Environment variable management.
- **Frontend**:
  - **HTML**: Structure.
  - **Tailwind CSS**: Styling.
  - **JavaScript**: Interactivity, API calls, progress updates.
- **Git LFS**: For managing large background video files.
- **FFmpeg**: Essential backend for MoviePy and Whisper (must be installed separately).

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
2.  **Install Git LFS:**
    - Download and install Git LFS from [git-lfs.github.com](https://git-lfs.github.com/) or use a package manager.
    - Initialize LFS for your user account (run once): `git lfs install`
    - Pull the large files tracked by LFS: `git lfs pull`
3.  **Create & Activate Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows: .\venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```
4.  **Install FFmpeg:**
    - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
    - Ensure the `ffmpeg` executable is in your system's PATH.
5.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    # Note: Whisper installation might take time as it includes PyTorch.
    ```
6.  **Set up Reddit API Credentials:**
    - Create a `.env` file in the _root_ directory (where README.md is).
    - Add your credentials:
    ```dotenv
    REDDIT_CLIENT_ID='your_client_id'
    REDDIT_CLIENT_SECRET='your_client_secret'
    REDDIT_USER_AGENT='your_user_agent' # e.g., 'ReelitApp by u/your_username'
    ```
7.  **Prepare Assets (Verify):**
    - The `assets/` directory should contain:
      - `background_gta.webm` (via Git LFS)
      - `background_minecraft.webm` (via Git LFS)
      - `background_subway_surfer.webm` (via Git LFS)
      - `background_music.mp3` (Your background music)
      - `title_template.png` (Your title card template)
      - `Inter-Bold.ttf` (Or your desired font file - update path in `src/video_creator.py` if different)

## Usage

1.  **Start the Server:**
    - Navigate to the `src` directory: `cd src`
    - Run the Flask app: `python app.py`
    - Keep this terminal running. It will show backend logs.
2.  **Open the Web UI:**
    - Open your web browser and go to `http://127.0.0.1:5000` (or the address shown in the terminal).
3.  **Generate Video:**
    - Enter a subreddit name.
    - Select a background video.
    - Adjust the music volume if desired.
    - Click "Generate Video".
4.  **Monitor & Retrieve:**
    - Watch the progress bar and logs directly in the web UI.
    - The first run might take longer as it downloads the Whisper model (`tiny.en` by default).
    - Once complete, the video player will appear.
    - Watch the video, download it, or generate another.
    - Final videos are also saved in the `output/` directory.

## Customization

- **Background Videos:** Add more `.webm` files to `assets/`, update the `BACKGROUND_VIDEOS` dictionary in `src/app.py`, and potentially track them with `git lfs track "*.webm"`.
- **Title Card Text:** Adjust font size range, color, boundary box in `draw_title_on_template` within `src/video_creator.py`.
- **Caption Style:** Modify font, size, colors, outline in `create_subtitle_image` within `src/video_creator.py`.
- **Caption Grouping:** Adjust `MAX_WORDS_PER_CAPTION` or `MIN_GAP_BETWEEN_CAPTIONS` in `create_video` within `src/video_creator.py`.
- **Whisper Model:** Modify `model_name` in `get_word_timestamps` call within `src/main.py` (e.g., to "base.en" for potentially better accuracy but slower speed).
- **Progress Steps/Weights:** Modify the `PIPELINE_STEPS` dictionary in `src/app.py` and update corresponding UI elements/logic if needed.
- **UI Styling:** Modify `src/templates/index.html` (Tailwind CSS classes) and `src/static/js/script.js`.
