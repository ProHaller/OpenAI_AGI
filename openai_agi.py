import argparse
import json
import os
from pathlib import Path
from tkinter import messagebox

from colorama import Fore, Style, init
from dotenv import dotenv_values, load_dotenv

import audio_utils
import openai_audio
import openai_text
import output_utils

# Initialize colorama
init(autoreset=True)
# Print text in different colors
# print(f"{Fore.RED}This is red text")
# print(f"{Fore.GREEN}This is green text")
# print(f"{Fore.YELLOW}This is yellow text")
# print(f"{Fore.BLUE}This is blue text")
# print(f"{Fore.MAGENTA}This is magenta text")
# print(f"{Fore.CYAN}This is cyan text")


# Function to ask user for environment variable
def ask_env_variable(var_name, mode="cli", parent=None):
    if mode == "gui" and parent is not None:
        # GUI mode
        print(f"Please set the variable: {var_name}")
    else:
        # CLI mode
        return input(f"Please enter your {var_name}: ")


def save_env_variable_gui(env_vars_values: tuple):
    with open(".env", "w", encoding="utf-8") as env_file:
        for var, value in env_vars_values:
            env_file.write(f"{var}={value}\n")
    check_env_variables()


def check_env_variables(mode="cli", parent=None):
    required_env_vars = ["OPENAI_API_KEY", "OPENAI_ORG"]
    missing_vars = {}

    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        open(".env", "a", encoding="utf-8").close()

    load_dotenv()

    for var in required_env_vars:
        env_value = os.getenv(var)
        # Check if the environment variable is missing, empty, or set to the string "None"
        if env_value in [None, "", "None"]:
            value = ask_env_variable(var, mode, parent)
            if value:  # Only update if a non-empty value is provided
                missing_vars[var] = value

    if missing_vars:
        env_vars = dotenv_values(".env")
        env_vars.update(missing_vars)

        with open(".env", "w", encoding="utf-8") as env_file:
            for var, value in env_vars.items():
                env_file.write(f"{var}={value}\n")

        load_dotenv()

    # Verification after updating .env file
    all_vars_set = all(
        os.getenv(var) not in [None, "", "None"] for var in required_env_vars
    )
    if all_vars_set:
        if mode == "cli":
            print("All required environment variables are set.")
        else:
            messagebox.showinfo("Info", "All required environment variables are set.")
        return all_vars_set
    if mode == "cli":
        print("Not all environment variables are set correctly.")
    else:
        messagebox.showerror(
            "Error", "Not all environment variables are set correctly."
        )
    return all_vars_set


def create_parser():
    parser = argparse.ArgumentParser(
        description="Audio Processing and Transcription Tool"
    )
    return parser


def setup_parser(parser):
    # Argument for specifying an audio file
    parser.add_argument("file", help="Path to the audio file", nargs="?", default=None)

    # Argument for specifying an output directory.
    parser.add_argument(
        "--output_directory",
        "-od",
        dest="output_directory",
        help="Path to the output directory, default to working directory.",
        nargs="?",
        default=None,
    )

    # Argument for specifying an output directory.
    parser.add_argument(
        "--output_filename",
        "-of",
        dest="output_filename",
        help="Path to the output filename, default to input filename.",
        nargs="?",
        default="output_file",
    )

    # Argument for specifying a language.
    parser.add_argument(
        "--language",
        "-l",
        dest="language",
        help="Language of the audio (ISO 639-1 code, \
        Ex: French = fr\n\
        English = en\n\
        Japanese = ja\n\
        Arabic = ar)",
        default="en",
    )

    # Argument for specifying a gpt model.
    parser.add_argument(
        "--model",
        "-m",
        dest="model",
        help="Specify a chat completion OpenAI model.\n\
        gpt-4-1106-preview, gpt-3.5-turbo\
        default to gpt-4",
        default="gpt-4-1106-preview",
    )

    # Argument for specifying a transcription output format.
    parser.add_argument(
        "--format",
        "-f",
        dest="format",
        choices=["json", "text", "srt", "verbose_json", "vtt"],
        help="Output format for the transcription",
        default="text",
    )

    # Argument for specifying a gpt model.
    parser.add_argument(
        "--temp",
        "-tp",
        dest="temperature",
        help=" Specify a temperature for gpt.\n\
        Default to: Unspecify",
        default=0.7,
    )

    # Argument for specifying a gpt model.
    parser.add_argument(
        "--tokenizer_name",
        "-tkn",
        dest="tokenizer_name",
        help=" Specify a tokenizer name for gpt.\
        Shouldn't be necesseray until update by OpenAI.\n\
        Default to: cl100k_base",
        default="cl100k_base",
    )

    # Options for audio pre-processing: trimming
    parser.add_argument(
        "--no_trim",
        "-nt",
        dest="trim",
        help="Prevent trimming the silence at the start of the file, recommended for srt output.",
        action="store_false",
        default=True,
    )

    # Specify the length of audio segments
    parser.add_argument(
        "--segment_duration_sec",
        "-sds",
        dest="segment_duration_sec",
        help="Specify the leght of audio segment duration in seconds,\
        defaults to 60 seconds.",
        default=60,
    )

    # Option for audio pre-processing: segmentation.
    parser.add_argument(
        "--no_segment",
        "-ns",
        dest="segment",
        help="Prevent the segmentation of the the audio file",
        action="store_false",
        default=True,
    )

    # Option for transcription post-processing: punctuation and formating cleaning.
    parser.add_argument(
        "--no_cleaning",
        "-nc",
        dest="cleaning",
        help="Prevent the cleaning of the the transcription. Default = False",
        action="store_false",
        default=True,
    )


# Load prompts from the JSON file
def load_prompts(prompts_file_path):
    with open(prompts_file_path, "r", encoding="utf-8") as file:
        prompt_list = json.load(file)
    return prompt_list


def parse_arguments():
    parser = create_parser()
    setup_parser(parser)
    return parser.parse_args()


def load_environment_variables():
    check_env_variables()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_org = os.getenv("OPENAI_ORG")
    return openai_api_key, openai_org


def initialize_openai_client(api_key, org):
    return openai_audio.init_openai_client(api_key, org)


def setup_output_directory(args):
    if args.output_directory is None:
        args.output_directory = str(Path.home() / "Downloads" / "Transcription")
    output_dir = Path(args.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"The output_directory is defaulting to {args.output_directory}.")
    return args.output_directory


def process_audio(client, prompts, args):
    if args:
        if args.file is None:
            openai_audio.create_audio(
                input("What is the script of the Audio?\n--> "), args.output_directory
            )
            exit()

        audio_prompt = input("\aDescribe the audio file (optional):\n-> ")
        audio_file_path = args.file
        trimmed_audio, _ = audio_utils.trim_start(audio_file_path)
        segments, segments_dir = audio_utils.segment_audio(
            trimmed_audio,
            args.segment_duration_sec * 1000,
            os.path.dirname(args.output_directory),
        )

        print("Audio file segmented.\nTranscribing..............")
        print(
            f"{Fore.BLUE}Segments: {segments}\nclient: {client}\nlanguage: {args.language}\naudio prompt: {audio_prompt}\nformat: {args.format}"
        )
        transcription = openai_audio.parallel_transcribe_audio(
            segments, client, args.language, audio_prompt, args.format
        )
        output_utils.save_to_file(transcription, args.file, args.output_directory)
        return transcription, audio_prompt, segments_dir


def clean_transcription(transcription, args, prompts):
    if not args.cleaning:
        return transcription

    tokenizer = openai_text.initialize_tokenizer(args.tokenizer_name)
    clean_transcriptions = []
    chunks = openai_text.create_chunks(transcription, 2000, tokenizer)
    cleaning_prompt = prompts["Punctuation assistant"]

    for chunk in chunks:
        clean_transcription = openai_text.openai_completion(
            "gpt-3.5-turbo",
            tokenizer.decode(chunk),
            cleaning_prompt,
        )
        clean_transcriptions.append(clean_transcription)

    cleaned_transcription = "\n".join(clean_transcriptions)
    output_utils.save_to_file(
        cleaned_transcription,
        f"clean_{os.path.basename(args.file)}",
        args.output_directory,
    )
    return cleaned_transcription


def create_secretary_note(args, cleaned_transcription, transcription, prompts):
    secretary_prompt = prompts["Personal assistant"] + input(
        "\aSecretary instructions : \n-> "
    )
    secretary_note = openai_text.openai_completion(
        args.model,
        cleaned_transcription or transcription,
        secretary_prompt,
        "json_object",
        args.temperature,
    )
    return output_utils.json_to_obsidian(secretary_note)


def main():
    args = parse_arguments()
    print("parsed args")
    openai_api_key, openai_org = load_environment_variables()
    print("set env")
    client = initialize_openai_client(openai_api_key, openai_org)
    print("set client")
    setup_output_directory(args)
    print("set output dir process to prompts loading")
    prompts = load_prompts("prompts.json")
    print("Loaded prompts process to transcription")
    transcription, audio_prompt, segments_dir = process_audio(client, prompts, args)
    print("transcription done")
    print(transcription)
    cleaned_transcription = clean_transcription(transcription, args, prompts)
    print("transcription cleaning done\n going to secretary note")
    (
        secretary_note_file,
        secretary_note_front,
        secretary_note_body,
    ) = create_secretary_note(args, cleaned_transcription, transcription, prompts)
    print("secretary note done. going to save")
    if input(
        "\nDo you want to save this note as an obsidian.md note? \n-> "
    ).lower() in ["y", "yes", "ok", "oui", "sure", "pourquoi pas", "aller"]:
        output_utils.save_to_file(
            str(secretary_note_front + secretary_note_body),
            secretary_note_file,
            args.output_directory,
            "md",
        )
    print("saved, …cleaning")

    if input("\nShould we clean up the audio segments?\n-> ").lower() in [
        "y",
        "yes",
        "ok",
        "oui",
        "sure",
        "pourquoi pas",
        "aller",
    ]:
        audio_utils.cleanup_directory(segments_dir)
    print(f"Cleaning {segments_dir}")


if __name__ == "__main__":
    main()
