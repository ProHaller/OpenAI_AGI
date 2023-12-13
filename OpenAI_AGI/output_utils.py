import json
import os
import shutil
from argparse import FileType
from datetime import datetime


def save_to_file(content, filename, output_directory, filetype="txt"):
    """
    Save the content to a file with the specified filename and filetype.
    """
    filename = os.path.basename(os.path.splitext(filename)[0])
    full_filename = os.path.join(output_directory, f"{filename}.{filetype}")
    # Create the output directory if it does not exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created directory: {output_directory}")

    try:
        with open(full_filename, "w", encoding="utf-8") as file:
            if filetype == "json":
                json.dump(content, file, ensure_ascii=False, indent=4)
            else:
                file.write(str(content))
        print("\n" * 3, f"File saved: {full_filename}.", "\n" * 3)
        return True
    except Exception as e:
        print(f"Error saving file {full_filename}: {e}")
        return False


def append_to_journal(operation, status, details, journal_file="operation_journal.txt"):
    """
    Append a record of an operation to the journal file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(journal_file, "a", encoding="utf-8") as file:
        file.write(
            f"{timestamp}: Operation '{operation}' - Status: {status}, Details: {details}\n"
        )


def json_to_obsidian(json_content):
    secretary_note = json.loads(json_content)
    secretary_note_file = secretary_note["File"]
    secretary_note_front = secretary_note["Front"]
    secretary_note_body = secretary_note["Body"]
    print(
        f"\a\
---> File name:\n {secretary_note_file}\n\n\n\
---> Front matter:\n {secretary_note_front}\n\n\n\
---> Note Body:\n {secretary_note_body}\
        "
    )
    return secretary_note_file, secretary_note_front, secretary_note_body
