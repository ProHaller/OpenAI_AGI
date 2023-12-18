# Imports: -----------------------------------------------------------------------------------------------------

import sys
import tkinter.filedialog as fd
from os import walk
from shutil import register_unpack_format
from tkinter import messagebox

import customtkinter as ctk

import audio_utils
import openai_agi
import openai_audio
import openai_text
import output_utils

# Set the theme for customtkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# Environment setting window: ---------------------------------------------------------------------------------


class EnvironmentSettingsPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Environment Settings")
        self.geometry("400x200")
        all_vars_set: bool = openai_agi.check_env_variables(mode="gui", parent=self)
        self.create_widgets()

    def create_widgets(self):
        self.api_key_label = ctk.CTkLabel(self, text="OPENAI API Key:")
        self.api_key_label.pack(pady=5)
        self.api_key_entry = ctk.CTkEntry(self)
        self.api_key_entry.pack(pady=5)

        self.org_label = ctk.CTkLabel(self, text="OPENAI ORG:")
        self.org_label.pack(pady=5)
        self.org_entry = ctk.CTkEntry(self)
        self.org_entry.pack(pady=5)

        self.save_button = ctk.CTkButton(self, text="Save", command=self.save_settings)
        self.save_button.pack(pady=10)

    def save_settings(self):
        required_env_vars = ["OPENAI_API_KEY", "OPENAI_ORG"]
        api_key_input = self.api_key_entry.get()
        org_input = self.org_entry.get()
        env_vars_values = (
            (required_env_vars[0], api_key_input),
            (required_env_vars[1], org_input),
        )
        # Securely save the API key and ORG to a config file or environment variable here
        # Example: save_to_configure(api_key_input, org_input)
        self.destroy()
        print(f"OpenAI Api Key: {api_key_input}\nOpenAI Org: {org_input}")
        openai_agi.save_env_variable_gui(env_vars_values)


# Left Panel Frame Class: --------------------------------------------------------------------------------------


class LeftPanelFrame(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.setup_title_label("Settings")
        self.setup_environment_settings_button()
        self.setup_file_selection_section()
        self.setup_output_folder_selection_section()
        self.setup_transcription_language()
        self.setup_prompt_selection()
        self.setup_prompt_section()
        self.setup_run_button()

    def setup_title_label(self, title):
        label = ctk.CTkLabel(self, text=title)
        label.pack(pady=10)

    def setup_environment_settings_button(self):
        self.env_settings_button = ctk.CTkButton(
            self,
            text="Environment Settings",
            command=self.open_environment_settings,
        )
        self.env_settings_button.pack(pady=10)

    def open_environment_settings(self):
        # Instantiating the EnvironmentSettingsPopup
        self.environment_popup = EnvironmentSettingsPopup(self)
        self.environment_popup.grab_set()  # Optional: to make the popup modal

    def setup_file_selection_section(self):
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=10)

        self.file_path_entry = ctk.CTkEntry(
            self.file_frame, placeholder_text="Select input file or folder", width=200
        )
        self.file_path_entry.pack(side="left", padx=10)

        self.browse_button = ctk.CTkButton(
            self.file_frame, text="Browse", command=self.browse_file
        )
        self.browse_button.pack(side="left", padx=10)

        # Confirmation label for displaying the selected file path
        self.confirmation_label = ctk.CTkLabel(self, text="")
        self.confirmation_label.pack(pady=5)

    def browse_file(self):
        file_path = fd.askopenfilename(
            title="Select a file or folder",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.m4a *.aac"),
                ("Text files", "*.txt *.md"),
                ("All folders", "*.*"),
            ],
        )

        if file_path:
            self.selected_file_path = file_path
            print(f"Input selected: {self.selected_file_path}")
            # Clear the existing text and insert the new file path
            self.file_path_entry.delete(0, "end")
            self.file_path_entry.insert(0, file_path)
            self.confirmation_label.configure(text=f"Selected: {file_path}")
        else:
            self.file_path_entry.delete(0, "end")
            self.confirmation_label.configure(text="No file selected")

    def setup_output_folder_selection_section(self):
        self.output_folder_frame = ctk.CTkFrame(self)
        self.output_folder_frame.pack(pady=10)

        self.output_folder_entry = ctk.CTkEntry(
            self.output_folder_frame,
            placeholder_text="Select output folder",
            width=200,
        )
        self.output_folder_entry.pack(side="left", padx=10)

        self.output_folder_browse_button = ctk.CTkButton(
            self.output_folder_frame, text="Browse", command=self.browse_output_folder
        )
        self.output_folder_browse_button.pack(side="left", padx=10)

        self.output_folder_confirmation_label = ctk.CTkLabel(self, text="")
        self.output_folder_confirmation_label.pack(pady=5)

    def browse_output_folder(self):
        folder_path = fd.askdirectory(title="Select output folder")

        if folder_path:
            self.selected_folder_path = folder_path
            print(f"Output folder selected: {self.selected_folder_path}")
            self.output_folder_entry.delete(0, "end")
            self.output_folder_entry.insert(0, folder_path)
            self.output_folder_confirmation_label.configure(
                text=f"Selected: {folder_path}"
            )
        else:
            self.output_folder_entry.delete(0, "end")
            self.output_folder_confirmation_label.configure(text="No folder selected")

    def setup_transcription_language(self):
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=10)

        self.language_label = ctk.CTkLabel(self.options_frame, text="Language:")
        self.language_label.pack(side="left", padx=10)

        language_values = ["English", "Japanese", "French", "Chinese", "Arabic"]
        self.language_menu = ctk.CTkOptionMenu(
            self.options_frame, values=language_values, command=self.update_language
        )
        self.language_menu.pack(side="left", padx=10)

        self.language_codes = {
            "English": "en",
            "Japanese": "ja",
            "French": "fr",
            "Chinese": "zh",
            "Arabic": "ar",
        }

        self.selected_language_code = None

    def update_language(self, selected_language):
        self.selected_language_code = self.language_codes[selected_language]
        print(f"Selected Language: {self.selected_language_code}")  # For demonstration

    def setup_prompt_selection(
        self, prompt_file_path="/Users/Haller/Dev/Python/OpenAI_AGI/prompts.json"
    ):
        self.prompt_select_frame = ctk.CTkFrame(self)
        self.prompt_select_frame.pack(pady=10)
        self.prompt_select_label = ctk.CTkLabel(
            self.prompt_select_frame, text="Prompt:"
        )
        self.prompt_select_label.pack(side="left", padx=10)

        prompt_pairs = openai_agi.load_prompts(prompt_file_path)
        self.prompt_menu = ctk.CTkOptionMenu(
            self.prompt_select_frame,
            values=tuple(prompt_pairs.keys()),
            command=self.update_prompt,
        )
        self.prompt_menu.pack(side="left", padx=10)

        self.prompt_texts = prompt_pairs  # (i for i in prompt_pairs.values())

        self.selected_prompt_title = None

    def update_prompt(self, selected_prompt_text):
        self.selected_prompt_title = self.prompt_texts[selected_prompt_text]
        print(f"Selected Prompt: {self.selected_prompt_title}")  # For demonstration
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("end", self.selected_prompt_title)

    def setup_prompt_section(self):
        self.prompt_frame = ctk.CTkFrame(self)
        self.prompt_frame.pack(pady=10, fill="both", expand=True)

        self.prompt_text = ctk.CTkTextbox(self.prompt_frame)
        self.prompt_text.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Placeholder text
        self.placeholder_text = "Enter prompt"
        self.prompt_text.insert("end", self.placeholder_text)
        self.prompt_text.bind("<FocusIn>", self.on_focus_in)
        self.prompt_text.bind("<FocusOut>", self.on_focus_out)

    def on_focus_in(self, event):
        if self.prompt_text.get("1.0", "end-1c").strip() == self.placeholder_text:
            self.prompt_text.delete("1.0", "end")

    def on_focus_out(self, event):
        if not self.prompt_text.get("1.0", "end-1c").strip():
            self.prompt_text.insert("end", self.placeholder_text)

    def setup_run_button(self):
        self.run_button = ctk.CTkButton(
            self, text="Run", command=self.start_transcription
        )
        self.run_button.pack(pady=20, side="bottom")

    def start_transcription(self):
        openai_api_key, openai_org = openai_agi.load_environment_variables()
        client = openai_agi.initialize_openai_client(openai_api_key, openai_org)
        transcription = openai_audio.transcribe_audio(
            self.selected_file_path,
            client,
            self.selected_language_code,
            self.prompt_texts,
            "text",
        )
        print(transcription)


# Transcription Output Frame Class: ---------------------------------------------------------------------------


class TranscriptionOutputFrame(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setup_title_label("Transcription")
        self.setup_transcription_output_text()

    def setup_title_label(self, title):
        label = ctk.CTkLabel(self, text=title)
        label.pack(pady=10)

    def setup_transcription_output_text(self):
        self.transcription_output_text = ctk.CTkTextbox(self)
        self.transcription_output_text.pack(expand=True, fill="both", padx=10, pady=10)


# Log Output Frame Class: --------------------------------------------------------------------------------------


class LogOutputFrame(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setup_title_label("Log")
        self.setup_log_output_text()
        sys.stdout = self

    def setup_title_label(self, title):
        label = ctk.CTkLabel(self, text=title)
        label.pack(pady=10)

    def setup_log_output_text(self):
        self.log_output_text = ctk.CTkTextbox(self, state="disabled")
        self.log_output_text.pack(expand=True, fill="both", pady=10, padx=10)

    def write(self, text):
        self.log_output_text.configure(state="normal")
        self.log_output_text.insert("end", text)
        self.log_output_text.configure(state="disabled")
        self.log_output_text.see("end")

    def flush(self):
        pass  # This is required for compatibility with file-like objects


# Main Application Class: --------------------------------------------------------------------------------------


class AudioTranscriptionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Audio Transcription App")
        self.geometry("1200x700")
        all_vars_set: bool = openai_agi.check_env_variables(mode="gui", parent=self)
        self.setup_ui_elements()

    def setup_ui_elements(self):
        self.left_panel = LeftPanelFrame(self)
        self.left_panel.grid(
            row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=10
        )

        self.grid_rowconfigure(0, weight=1)  # Weight for transcription output frame
        self.grid_rowconfigure(1, weight=1)  # Weight for transcription output frame
        self.grid_rowconfigure(2, weight=1)  # Weight for log output frame

        self.grid_columnconfigure(0, weight=0)  # Fixed width for left panel
        self.grid_columnconfigure(
            1, weight=1
        )  # Allow horizontal expansion for other frames

        self.transcription_output_frame = TranscriptionOutputFrame(self)
        self.transcription_output_frame.grid(
            row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10
        )

        self.log_output_frame = LogOutputFrame(self)
        self.log_output_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)


if __name__ == "__main__":
    app = AudioTranscriptionApp()
    app.mainloop()
