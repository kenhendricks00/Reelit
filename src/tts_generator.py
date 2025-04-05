from gtts import gTTS
import os

def create_narration(text, output_filename):
    """Generates narration audio from text using gTTS and saves it as an MP3 file.

    Args:
        text (str): The text to convert to speech.
        output_filename (str): The path (including filename) to save the MP3 file.
    """
    try:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")

        tts = gTTS(text=text, lang='en', slow=False) # Using English, normal speed
        tts.save(output_filename)
        print(f"Narration audio saved successfully to {output_filename}")
        return True
    except Exception as e:
        print(f"Failed to create narration audio: {e}")
        return False

if __name__ == '__main__':
    # Example usage:
    example_text = "Hello, this is a test of the Google Text-to-Speech library. We are creating an audio file."
    output_file = "output/test_narration.mp3" 

    # Create the output directory if it doesn't exist for the example
    if not os.path.exists("output"):
        os.makedirs("output")
        
    if create_narration(example_text, output_file):
        print("Example narration created.")
    else:
        print("Failed to create example narration.") 