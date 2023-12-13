import argparse
import glob
import json
import os

import audio_utils
import openai_audio
import openai_text
import output_utils
from dotenv import dotenv_values, load_dotenv


# Function to ask user for environment variable
def ask_env_variable(var_name):
    value = input(f"Please enter your {var_name}: ")
    return value


def check_env_variables():
    required_env_vars = ["OPENAI_API_KEY", "OPENAI_ORG"]
    missing_vars = {}

    # Load existing .env file
    load_dotenv()

    # Identify missing environment variables
    for var in required_env_vars:
        if not os.getenv(var):
            value = ask_env_variable(var)
            missing_vars[var] = value

    # Update .env file if there are missing variables
    if missing_vars:
        # Read current .env file content
        env_vars = dotenv_values(".env")
        env_vars.update(missing_vars)

        # Write updated environment variables to .env file
        with open(".env", "w", encoding="utf-8") as env_file:
            for var, value in env_vars.items():
                env_file.write(f"{var}={value}\n")

        # Reload the .env file to update environment variables
        load_dotenv()

        # Verify that the variables have been set
        for var in missing_vars:
            if not os.getenv(var):
                raise ValueError(f"Failed to set environment variable: {var}")

    print("All required environment variables are set.")


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
        "--clean",
        "-c",
        dest="clean",
        help="Clean the the transcription. Default = False",
        action="store_true",
        default=False,
    )


# def on_keyboard_interrupt():
#     print("Keyboard interrupt detected! Running cleanup function.")
# try:
#     while True:
#         print("Program is running. Press Ctrl+C to stop.")
#         time.sleep(1)  # Simulate a long-running process
# except KeyboardInterrupt:
#     on_keyboard_interrupt()


# Load prompts from the JSON file
def load_prompts(prompts_file_path):
    with open(prompts_file_path, "r", encoding="utf-8") as file:
        prompt_list = json.load(file)
    return prompt_list


# Assuming the file is named 'prompts.json' in the same directory as your script
prompts = load_prompts("prompts.json")


def main():
    parser = create_parser()
    setup_parser(parser)
    args = parser.parse_args()

    check_env_variables()

    # Load environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_org = os.getenv("OPENAI_ORG")

    # Initialize OpenAI client
    client = openai_audio.init_openai_client(openai_api_key, openai_org)

    output_directory = args.output_directory or os.path.join(
        os.path.dirname(args.file), os.path.basename(args.file) + "_output"
    )
    os.makedirs(output_directory, exist_ok=True)
    print(f"The output_directory is defaulting to {output_directory}.")

    # Create audio from a prompt if no audio is provided.
    if args.file is None:
        openai_audio.create_audio(
            input("What is the script of the Audio?\n--> "), output_directory
        )
        exit()

    if os.path.isdir(args.file):
        file_list = glob.glob(os.path.join(args.file, "*"))
        for f in file_list:
            if os.path.isfile(f):
                trimmed_audio, _ = audio_utils.trim_start(f)
                segments, segments_dir = audio_utils.segment_audio(
                    trimmed_audio, 60000, os.path.dirname(f)
                )
                transcription = openai_audio.parallel_transcribe_audio(segments, client)
                output_utils.save_to_file(transcription, f, args.file)
                audio_utils.cleanup_directory(segments_dir)
        exit()

    audio_prompt = input("\aDescribe the audio file (optional):\n-> ")
    cleaning_prompt = prompts["punctuation_assistant"]
    audio_file_path = args.file
    trimmed_audio, _ = audio_utils.trim_start(audio_file_path)

    # Define segment duration (e.g., 1 minute)
    segment_duration_ms = args.segment_duration_sec * 1000
    segments, segments_dir = audio_utils.segment_audio(
        trimmed_audio, segment_duration_ms, os.path.dirname(args.file)
    )
    print(
        "..............Audio file segmented, transcribing..............",
    )
    # Transcribe each audio segment
    transcription = openai_audio.parallel_transcribe_audio(
        segments,
        client,
        language=args.language,
        prompt=audio_prompt,
        response_format=args.format,
    )

    print(
        f"This is the transcription of {args.file}({args.language}):\n\n\
        {transcription}",
    )
    output_utils.save_to_file(transcription, args.file, output_directory)

    clean_full_transcription = ""
    # Process the text
    if args.clean is True:
        # Initialize Tokenizer
        tokenizer_name = args.tokenizer_name
        tokenizer = openai_text.initialize_tokenizer(tokenizer_name)

        # Clean transcription
        clean_transcriptions = []
        chunks = openai_text.create_chunks(transcription, 2000, tokenizer)
        text_chunks = [tokenizer.decode(chunk) for chunk in chunks]
        for chunk in text_chunks:
            clean_transcription = openai_text.openai_completion(
                "gpt-3.5-turbo",
                chunk,
                cleaning_prompt,
            )
            clean_transcriptions.append(clean_transcription)

        # Concatenate transcriptions
        clean_full_transcription = "\n".join(clean_transcriptions)
        print(
            f"This is the cleaned transcription:\n\n {clean_full_transcription}",
        )

        # Output the results
        output_utils.save_to_file(
            clean_full_transcription,
            f"clean_{os.path.basename(args.file)}",
            output_directory,
        )

    # Secretary note
    # todo Probably should externalize secretary note
    # todo Need to define secretary_prompt somewhere.

    user_input = input(
        "\nDo you want to generate a secretary note from this transcription? \n-> "
    ).lower()
    if user_input in ["y", "yes", "ok", "oui", "sure", "pourquoi pas", "aller"]:
        secretary_prompt = prompts["roland_haller_assistant"] + input(
            "\aSecretary instructions : \n-> "
        )
        secretary_note = openai_text.openai_completion(
            args.model,
            (clean_full_transcription if clean_full_transcription else transcription),
            secretary_prompt,
            "json_object",
            args.temperature,
        )
        (
            secretary_note_file,
            secretary_note_front,
            secretary_note_body,
        ) = output_utils.json_to_obsidian(secretary_note)
        user_input = input(
            "\nDo you want to save this note as an obsidian.md note? \n-> "
        ).lower()
        if user_input in ["y", "yes", "ok", "oui", "sure", "pourquoi pas", "aller"]:
            # Output the results
            secretary_note_filetype = "md"
            output_utils.save_to_file(
                str(secretary_note_front + secretary_note_body),
                secretary_note_file,
                args.output_directory,
                secretary_note_filetype,
            )
        user_input = input("\nShould we clean up the audio segments?\n-> ").lower()
        if user_input in ["y", "yes", "ok", "oui", "sure", "pourquoi pas", "aller"]:
            print(f"Cleaning: {args.output_directory}, {segments_dir}…")
            print(args.output_directory, segments_dir)
            audio_utils.cleanup_directory(args.output_directory, segments_dir)
    else:
        print(f"Cleaning: {args.output_directory}, {segments_dir}…")
        audio_utils.cleanup_directory(output_directory or segments_dir)


if __name__ == "__main__":
    main()
