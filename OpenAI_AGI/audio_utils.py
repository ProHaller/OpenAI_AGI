import json
import os
import shutil
from pathlib import Path

from pydub import AudioSegment


# Function to detect leading silence
def milliseconds_until_sound(sound, silence_threshold_in_decibels=-20.0, chunk_size=10):
    trim_ms = 0  # ms
    assert chunk_size > 0  # to avoid infinite loop
    while sound[
        trim_ms : trim_ms + chunk_size
    ].dBFS < silence_threshold_in_decibels and trim_ms < len(sound):
        trim_ms += chunk_size
    return trim_ms


# Function to trim the start of an audio file
def trim_start(filepath):
    path = Path(filepath)
    directory = path.parent
    filename = path.stem
    trimmed_directory = directory / f"{filename}/trimmed_audio"
    trimmed_directory.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_file(filepath)
    start_trim = milliseconds_until_sound(audio)
    trimmed_audio = audio[start_trim:]
    trimmed_filename = trimmed_directory / f"trimmed_{path.name}"
    trimmed_audio.export(trimmed_filename, format="wav")
    trimmed_audio = AudioSegment.from_file(trimmed_filename)
    return trimmed_audio, trimmed_filename


# Function to segment an audio file
def segment_audio(trimmed_audio, segment_duration_ms, output_dir):
    start_time = 0
    segments = []
    while start_time < len(trimmed_audio):
        segment = trimmed_audio[start_time : start_time + segment_duration_ms]
        segment_filename = os.path.join(
            output_dir, f"segment_{start_time // 1000:02d}.wav"
        )
        segment.export(segment_filename, format="wav")
        segments.append(segment_filename)
        start_time += segment_duration_ms
    return segments


# Function to clean up a directory
def cleanup_directory(dir_path):
    if os.path.isdir(dir_path):
        try:
            shutil.rmtree(dir_path)
            return True, "Directory successfully deleted."
        except Exception as e:
            return False, f"Error occurred while deleting the directory: {e}"
    else:
        return False, "Directory does not exist or has already been deleted."
