import moviepy.editor as mp
import os
import math
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re

# --- Helper Functions ---

def split_text(text, max_words_per_chunk=5):
    """Splits text into chunks with a max number of words."""
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words_per_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk: # Add any remaining words
        chunks.append(" ".join(current_chunk))
    return chunks

# Added function to draw title onto the template
def draw_title_on_template(template_path, title_text, output_path,
                           font_path='src/assets/Inter-Bold.ttf', 
                           max_font_size=48, min_font_size=36, 
                           text_color=(0, 0, 0), 
                           boundary_x=150, boundary_y=910, 
                           boundary_width=780, boundary_max_height=160,
                           debug_boundary=True):
    """Loads template, draws title adaptively within a defined boundary.
    Adjust boundary_x/y/width/max_height as needed for your template.
    """
    print(f"Drawing adaptive title '{title_text[:30]}...' onto template within boundary...")
    try:
        img = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # Draw the boundary box for debugging
        if debug_boundary:
            boundary_color = (255, 0, 0, 128)  # Semi-transparent red
            draw.rectangle(
                [(boundary_x, boundary_y), 
                 (boundary_x + boundary_width, boundary_y + boundary_max_height)],
                outline=boundary_color,
                width=3
            )
            print(f"Drawing debug boundary box at: ({boundary_x}, {boundary_y}, {boundary_width}, {boundary_max_height})")

        # width, height = img.size # Get image dimensions if needed, but boundary is primary

        font = None
        wrapped_text = ""
        text_width = 0
        text_height = 0
        final_font_size = max_font_size

        # --- Find optimal font size --- 
        for current_font_size in range(max_font_size, min_font_size - 1, -2): 
            try:
                current_font = ImageFont.truetype(font_path, current_font_size)
            except IOError:
                if current_font_size <= min_font_size:
                    print(f"Warning: Font '{font_path}' not found in assets. Trying default Arial...")
                    try: font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', max_font_size)
                    except IOError: 
                        print("Warning: Arial not found. Using default Pillow font.")
                        font = ImageFont.load_default()
                    final_font_size = max_font_size
                    break
                else:
                    continue
            
            # Wrap text based on BOUNDARY width
            avg_char_width = current_font_size / 1.7  # Slightly reduced for better wrapping
            # Use boundary_width for wrapping calculation
            max_chars = math.floor(boundary_width / avg_char_width) if avg_char_width > 0 else 10
            if max_chars <= 0: max_chars = 10
            current_wrapped_text = textwrap.fill(title_text, width=max_chars)

            # Calculate text block dimensions for this size
            current_bbox = draw.textbbox((0, 0), current_wrapped_text, font=current_font)
            current_text_width = current_bbox[2] - current_bbox[0]
            current_text_height = current_bbox[3] - current_bbox[1]

            # Check if it fits within the BOUNDARY height
            if current_text_height <= boundary_max_height:
                font = current_font
                wrapped_text = current_wrapped_text
                text_width = current_text_width
                text_height = current_text_height # Store final height
                final_font_size = current_font_size
                print(f"  Fit found with font size: {final_font_size}, height: {current_text_height}")
                break 
            elif current_font_size == min_font_size:
                 print(f"Warning: Text might be too large even at min font size {min_font_size}. Using smallest size.")
                 font = current_font
                 wrapped_text = current_wrapped_text
                 text_width = current_text_width
                 text_height = current_text_height # Store final height
                 final_font_size = current_font_size
        # --- End Font Size Loop --- 
        
        # --- Calculate Final Position within BOUNDARY --- 
        # Center horizontally within the boundary
        x = boundary_x + (boundary_width - text_width) / 2
        
        # Center vertically within the boundary
        y = boundary_y + (boundary_max_height - text_height) / 2

        # --- Draw Text --- 
        print(f"  Drawing text block at ({x:.0f}, {y:.0f}) with size {final_font_size}")
        draw.text((x, y), wrapped_text, font=font, fill=text_color, align="center")

        # --- Save Image --- 
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        img.save(output_path, "PNG")
        print(f"Custom title card saved to {output_path}")
        return True, output_path

    except Exception as e:
        print(f"Error drawing adaptive title on template: {e}")
        import traceback
        traceback.print_exc()
        return False, None

# Updated function to create subtitle images using Pillow (No wrapping)
def create_subtitle_image(text, output_path, width, # width param might become less relevant now
                          font_path='src/assets/Montserrat-Black.ttf', 
                          font_size=90, text_color=(255, 255, 255),
                          padding=20, 
                          outline_color=(0, 0, 0), outline_width=2):
    """Creates a transparent PNG image for a subtitle chunk (single line).
    Features white text with a black outline.
    """
    try:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            print(f"Warning: Subtitle Font '{font_path}' not found in assets. Trying default Arial...")
            try:
                 font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', font_size)
            except IOError:
                print("Warning: Arial font not found either. Using default Pillow font for subtitles.")
                font = ImageFont.load_default()

        # --- Remove Text wrapping --- 
        # avg_char_width = font_size / 1.8
        # max_chars_per_line = math.floor((width - 2 * padding) / avg_char_width)
        # if max_chars_per_line <= 0: max_chars_per_line = 10
        # wrapped_text = textwrap.fill(text, width=max_chars_per_line)
        # Use the raw text chunk directly
        unwrapped_text = text 

        # Determine text bounding box using the unwrapped text
        text_bbox = font.getbbox(unwrapped_text) 
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1] 

        # Add padding for outline and spacing
        effective_padding_x = padding + outline_width
        effective_padding_y = padding + outline_width + int(font_size * 0.1) # Extra bottom padding
        img_width = text_width + 2 * effective_padding_x
        img_height = text_height + 2 * effective_padding_y
        
        # Create TRANSPARENT image 
        img = Image.new('RGBA', (img_width, img_height), color=(0, 0, 0, 0)) 
        draw = ImageDraw.Draw(img)

        # --- Draw Outline --- 
        draw_x = effective_padding_x
        draw_y = effective_padding_y - text_bbox[1] # Adjust y by the bbox top offset
        for x_offset in range(-outline_width, outline_width + 1):
            for y_offset in range(-outline_width, outline_width + 1):
                if x_offset == 0 and y_offset == 0:
                    continue
                # Draw outline using unwrapped text
                draw.text((draw_x + x_offset, draw_y + y_offset), 
                          unwrapped_text, font=font, fill=outline_color, align="left") # Align doesn't matter much for single line

        # --- Draw Main Text (Centered horizontally by drawing coords) --- 
        # Draw main text using unwrapped text
        draw.text((draw_x, draw_y), 
                  unwrapped_text, font=font, fill=text_color, align="left") # Align doesn't matter much for single line

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        img.save(output_path, "PNG")
        # print(f"Subtitle image saved: {output_path}") # Optional: reduce logging
        return True, output_path

    except Exception as e:
        print(f"Error creating subtitle image for '{text[:20]}...': {e}")
        return False, None

# --- Main Video Creation Function ---

def create_video(audio_path, background_video_path, title_text, story_text, 
                 word_timestamps, music_path, output_path, 
                 target_aspect_ratio=9/16, music_volume=0.15):
    """Combines narration, background video, title card, captions, and background music.
    
    Args:
        audio_path (str): Path to the narration audio file.
        background_video_path (str): Path to the background video file.
        title_text (str): Original title text for visual card.
        story_text (str): Original story text (used for reference, not timing).
        word_timestamps (list): List of {'word', 'start', 'end'} dicts from Whisper.
        music_path (str or None): Path to the background music file, or None.
        output_path (str): Path to save the output video file.
        target_aspect_ratio (float): Target aspect ratio for the video.
        music_volume (float): Volume multiplier for background music (0.0 to 1.0).

    Returns:
        bool: True if video creation was successful, False otherwise.
    """
    # Define fixed video dimensions for 9:16
    target_width = 1080
    target_height = 1920
    # Adjust default template path
    title_template_path = "src/assets/title_template.png"
    temp_titled_card_path = os.path.join(os.path.dirname(output_path), "temp_titled_card.png")

    # Initialize clips
    narration_clip = None # Renamed from audio_clip for clarity
    music_clip = None
    composite_audio = None
    video_clip = None
    title_card_clip = None
    subtitle_clips = []
    temp_subtitle_files = []
    final_clip = None

    try:
        print(f"Starting video creation with background music...")

        # 1. Load Narration Audio
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Narration audio file not found: {audio_path}")
        narration_clip = mp.AudioFileClip(audio_path)
        narration_duration = narration_clip.duration # Use this as the main duration reference
        print(f"Narration audio loaded. Duration: {narration_duration:.2f} seconds")

        # 2. Load Background Music (if path provided)
        if music_path and os.path.exists(music_path):
            print(f"Loading background music from: {music_path}")
            music_clip = mp.AudioFileClip(music_path)
            print(f"  Original music duration: {music_clip.duration:.2f}s")
            # Reduce volume
            music_clip = music_clip.volumex(music_volume)
            print(f"  Music volume adjusted to {music_volume*100}%")
            # Loop if necessary
            if music_clip.duration < narration_duration:
                loops = int(narration_duration / music_clip.duration) + 1
                music_clip = mp.concatenate_audioclips([music_clip] * loops)
                print(f"  Music looped {loops} times.")
            # Trim to narration duration
            music_clip = music_clip.subclip(0, narration_duration)
            print(f"  Music trimmed to narration duration: {music_clip.duration:.2f}s")
            # Create composite audio
            composite_audio = mp.CompositeAudioClip([narration_clip, music_clip])
            print("Narration and background music combined.")
        else:
            if music_path:
                print(f"Warning: Background music file not found at '{music_path}'. Skipping music.")
            else:
                print("No background music path provided. Skipping music.")
            # Use only narration if no music
            composite_audio = narration_clip 

        # 3. Estimate Title Speak Duration (using word timestamps)
        spoken_title_text = re.sub(r'\bAITA\b\??', 'Am I the asshole?', title_text, flags=re.IGNORECASE)
        spoken_title_word_list = spoken_title_text.split()
        title_word_count = len(spoken_title_word_list)
        estimated_title_speak_duration = 0
        if title_word_count > 0 and len(word_timestamps) >= title_word_count:
            try:
                 estimated_title_speak_duration = word_timestamps[title_word_count - 1]['end']
            except IndexError:
                 total_narration_word_count = len(word_timestamps)
                 if total_narration_word_count > 0:
                     estimated_title_speak_duration = (title_word_count / total_narration_word_count) * narration_duration
                 else: 
                     estimated_title_speak_duration = 3.0
        else:
             estimated_title_speak_duration = 3.0 
        if estimated_title_speak_duration < 0.1: estimated_title_speak_duration = 0.5
        print(f"  Estimated title end time from Whisper: {estimated_title_speak_duration:.2f}s")

        # 4. Create Dynamic Title Card Image
        success, final_title_card_path = draw_title_on_template(
            title_template_path, 
            title_text, 
            temp_titled_card_path,
            max_font_size=48,
            min_font_size=36,
            boundary_x=150,
            boundary_y=910,
            boundary_width=780,
            boundary_max_height=160,
            debug_boundary=False  # Turn off debugging for production
        )
        if not success: raise RuntimeError("Failed to create dynamic title card image.")
        title_card_clip = mp.ImageClip(final_title_card_path)
        title_card_clip = title_card_clip.set_duration(estimated_title_speak_duration) 
        title_card_clip = title_card_clip.set_position(('center', 'center'))
        title_card_clip = title_card_clip.set_start(0)
        print(f"Dynamic title card configured for duration: {estimated_title_speak_duration:.2f}s.")

        # 5. Load and Prepare Background Video (using narration_duration)
        if not os.path.exists(background_video_path): raise FileNotFoundError(f"BG video not found: {background_video_path}")
        video_clip = mp.VideoFileClip(background_video_path)
        if video_clip.duration < narration_duration:
            num_loops = int(narration_duration // video_clip.duration) + 1
            video_clip = mp.concatenate_videoclips([video_clip] * num_loops)
        video_clip = video_clip.subclip(0, narration_duration)
        video_clip = video_clip.resize(height=target_height)
        crop_width_bg = target_width
        x_center_bg = video_clip.w / 2
        x1_bg = x_center_bg - crop_width_bg / 2
        video_clip = video_clip.crop(x1=x1_bg, width=crop_width_bg)

        # 6. Generate Subtitle Images and Clips using Whisper Timestamps
        print("Generating subtitle images and clips using Whisper timestamps...")
        MAX_WORDS_PER_CAPTION = 2 # Reduced words per chunk
        MIN_GAP_BETWEEN_CAPTIONS = 0.1 
        output_dir = os.path.dirname(output_path)
        base_filename = os.path.splitext(os.path.basename(output_path))[0]
        current_chunk_words = []
        chunk_start_time = -1
        last_word_end_time = 0
        story_word_timestamps = word_timestamps[title_word_count:]
        if not story_word_timestamps:
            print("Warning: No word timestamps remaining after skipping estimated title words.")
        else:
             chunk_start_time = story_word_timestamps[0]['start'] 
             print(f"  Starting first story caption around: {chunk_start_time:.2f}s")
             for i, word_info in enumerate(story_word_timestamps):
                 word_text = word_info['word']
                 start_time = word_info['start']
                 end_time = word_info['end']
                 is_new_chunk = False
                 if not current_chunk_words: is_new_chunk = True
                 elif len(current_chunk_words) >= MAX_WORDS_PER_CAPTION: is_new_chunk = True
                 elif (start_time - last_word_end_time) >= MIN_GAP_BETWEEN_CAPTIONS: is_new_chunk = True
                 if is_new_chunk and current_chunk_words:
                     chunk_text = " ".join(current_chunk_words)
                     chunk_end_time = last_word_end_time
                     chunk_duration = chunk_end_time - chunk_start_time
                     if chunk_duration <= 0.05: chunk_duration = 0.1
                     temp_img_path = os.path.join(output_dir, f"{base_filename}_temp_sub_{len(subtitle_clips)}.png")
                     success, img_path = create_subtitle_image(chunk_text, temp_img_path, width=target_width - 100)
                     if success:
                         temp_subtitle_files.append(img_path)
                         img_clip = mp.ImageClip(img_path, ismask=False, transparent=True)
                         img_clip = img_clip.set_start(chunk_start_time)
                         img_clip = img_clip.set_duration(chunk_duration)
                         img_clip = img_clip.set_position(('center', 'center'))
                         subtitle_clips.append(img_clip)
                         print(f"    Created caption: '{chunk_text}' @ {chunk_start_time:.2f}s (Duration: {chunk_duration:.2f}s)")
                     else: print(f"    Skipping caption '{chunk_text}' due to image error.")
                     current_chunk_words = [word_text]
                     chunk_start_time = start_time
                 else:
                     current_chunk_words.append(word_text)
                     if len(current_chunk_words) == 1: chunk_start_time = start_time
                 last_word_end_time = end_time
             if current_chunk_words:
                 chunk_text = " ".join(current_chunk_words)
                 chunk_end_time = last_word_end_time
                 chunk_duration = chunk_end_time - chunk_start_time
                 if chunk_duration <= 0.05: chunk_duration = 0.1
                 temp_img_path = os.path.join(output_dir, f"{base_filename}_temp_sub_{len(subtitle_clips)}.png")
                 success, img_path = create_subtitle_image(chunk_text, temp_img_path, width=target_width - 100)
                 if success:
                     temp_subtitle_files.append(img_path)
                     img_clip = mp.ImageClip(img_path, ismask=False, transparent=True)
                     img_clip = img_clip.set_start(chunk_start_time)
                     img_clip = img_clip.set_duration(chunk_duration)
                     img_clip = img_clip.set_position(('center', 'center'))
                     subtitle_clips.append(img_clip)
                     print(f"    Created final caption: '{chunk_text}' @ {chunk_start_time:.2f}s (Duration: {chunk_duration:.2f}s)")
                 else: print(f"    Skipping final caption '{chunk_text}' due to image error.")

        # 7. Composite Video
        print("Compositing final video...")
        clips_to_composite = [video_clip, title_card_clip] + subtitle_clips
        final_clip = mp.CompositeVideoClip(clips_to_composite, size=(target_width, target_height))
        
        # Set the COMPOSITE audio (narration + music)
        final_clip = final_clip.set_audio(composite_audio) 
        print("Video layers composited and final audio attached.")

        # 8. Write Final Video
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        print(f"Writing final video to {output_path}...")
        final_clip.write_videofile(
            output_path, codec='libx264', audio_codec='aac',
            temp_audiofile='temp-audio.m4a', remove_temp=True,
            preset='medium', ffmpeg_params=["-crf", "23"], threads=4
        )

        print(f"Video created successfully: {output_path}")
        return True

    except Exception as e:
        print(f"An error occurred during video creation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("Cleaning up resources...")
        # Close all clips
        if narration_clip: narration_clip.close()
        if music_clip: music_clip.close()
        # CompositeAudioClip doesn't have explicit close, components closed above/below
        if video_clip: video_clip.close()
        if title_card_clip: title_card_clip.close()
        for clip in subtitle_clips: 
            if hasattr(clip, 'reader'): clip.close()
            elif hasattr(clip, 'close'): clip.close()
        if final_clip and hasattr(final_clip, 'close'): final_clip.close()
        # Remove temp files
        print(f"Cleaning up {len(temp_subtitle_files)} temporary subtitle images...")
        for temp_file in temp_subtitle_files:
            if os.path.exists(temp_file):
                try: os.remove(temp_file)
                except OSError as e: print(f"Error removing temp subtitle file {temp_file}: {e}")
        if os.path.exists(temp_titled_card_path):
            try: 
                os.remove(temp_titled_card_path)
                print(f"Removed temp dynamic title card: {temp_titled_card_path}")
            except OSError as e: print(f"Error removing temp dynamic title card {temp_titled_card_path}: {e}")

# --- Example Usage Update --- 
if __name__ == '__main__':
    # Example paths need adjustment
    print("Running video creation example with background music...")
    example_title = "AITA for testing background music?"
    example_story = "This test includes background music layered with narration."
    example_narration_raw = f"{example_title} {example_story}"
    example_narration_for_tts = re.sub(r'\bAITA\b\??', 'Am I the asshole?', example_narration_raw, flags=re.IGNORECASE)
    narration_file = "src/output/test_narration_music.mp3" # Relative to src
    background_file = "src/assets/background.mp4" # Relative to src
    music_file = "src/assets/background_music.mp3" # Relative to src
    output_video_file = "src/output/final_video_with_music.mp4" # Relative to src
    template_file_check = "src/assets/title_template.png" # Relative to src
    example_font_path = "src/assets/Montserrat-Black.ttf" # Relative to src

    # Ensure dirs exist relative to src
    if not os.path.exists("src/output"): os.makedirs("src/output")
    if not os.path.exists("src/assets"): os.makedirs("src/assets")
    
    # Create narration for example if it doesn't exist
    if not os.path.exists(narration_file):
        print(f"Creating dummy narration for example: {narration_file}")
        try:
            # Assuming tts_generator is in the same directory (src)
            from tts_generator import create_narration 
            if not create_narration(example_narration_for_tts, narration_file):
                 raise RuntimeError("Failed using tts_generator for example")
        except ImportError:
            print("Error: Could not import tts_generator. Make sure it's in the src directory.")
            exit(1)
        except Exception as e:
            print(f"Error creating example narration: {e}")
            exit(1)
            
    # Check other files using adjusted paths
    if not os.path.exists(background_file): print(f"Error: BG video not found: {background_file}"); exit(1)
    if not os.path.exists(template_file_check): print(f"Error: Template not found: {template_file_check}"); exit(1)
    # Check font file for example
    if not os.path.exists(example_font_path): print(f"Warning: Font file for example not found: {example_font_path}")
    # Check music file
    example_music_path = None
    if os.path.exists(music_file): 
        example_music_path = music_file
    else:
        print(f"Warning: Example music file not found: {music_file}. Running example without music.")
        
    # Get Timestamps for Example 
    example_timestamps = None
    try:
        # Assuming alignment is in the same directory (src)
        from alignment import get_word_timestamps 
        example_timestamps = get_word_timestamps(narration_file)
        if not example_timestamps:
             raise RuntimeError("Failed to get timestamps from alignment module for example.")
    except ImportError:
        print("Error: Could not import alignment. Make sure it's in the src directory.")
        exit(1)
    except Exception as e:
        print(f"Error getting timestamps for example: {e}")
        exit(1)
        
    # Run video creation
    if create_video(narration_file, background_file, example_title, example_story, example_timestamps, example_music_path, output_video_file):
        print("Example video with background music created successfully.")
    else:
        print("Failed to create example video with background music.") 