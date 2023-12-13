import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import openai
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG = os.getenv("OPENAI_ORG")
openai.api_key = OPENAI_API_KEY

# client = OpenAI(
#     organization=OPENAI_ORG,
# )


# Initialize OpenAI client
def init_openai_client(api_key, organization):
    openai.api_key = api_key
    return openai.OpenAI(organization=organization)


# Function for transcribing audio
def transcribe_audio(file_path, client, language, prompt, response_format):
    try:
        with open(file_path, "rb") as audio_file:
            transcription_data = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format=response_format,
            )
            return transcription_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Function for generating voice from text
def create_audio(
    input_text,
    output_directory="speech_file_path",
    speed=1.0,
    voice="onyx",
    model="tts-1-hd",
    response_format="mp3",
):
    speech_file_path = Path(output_directory) / "speech.mp3"
    try:
        response = openai.audio.speech.create(
            model=model,
            voice=voice,
            speed=speed,
            response_format=response_format,
            input=input_text,
        )
        response.stream_to_file(speech_file_path)
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


# Function for parallel audio transcription
def parallel_transcribe_audio(
    file_paths,
    client,
    language="en",
    prompt="",
    response_format="text",
    max_workers=10,
):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a list of futures with their corresponding index
        futures = {
            executor.submit(
                transcribe_audio, file_path, client, language, prompt, response_format
            ): i
            for i, file_path in enumerate(file_paths)
        }

    # Collect the transcription data as they complete, with their corresponding index
    transcriptions = {}
    for future in futures:
        try:
            transcription_data = future.result()  # Get the result from the future
            index = futures[future]  # Get the index of the future
            transcriptions[index] = transcription_data
        except Exception as e:
            print(f"An error occurred: {e}")

    # Sort transcriptions by index and combine into a single transcript
    sorted_transcription_texts = [
        transcriptions[i]
        for i in sorted(transcriptions)
        if transcriptions[i] is not None
    ]
    full_transcript = " ".join(sorted_transcription_texts)
    return full_transcript
