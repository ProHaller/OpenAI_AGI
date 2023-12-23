# Imports: -----------------------------------------------------------------------------------------------------

import datetime
import json
import logging
import os
import sys
import threading
import tkinter.filedialog as fd
from tkinter import messagebox

import customtkinter as ctk
import env_utils
import openai_audio
import openai_text

# Set the theme for customtkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

# Environment setting window: ---------------------------------------------------------------------------------


class EnvironmentSettingsPopup(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Environment Settings")
        self.geometry("400x200")
        all_vars_set: bool = env_utils.check_env_variables(mode="gui", parent=self)
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
        env_utils.save_env_variable_gui(env_vars_values)


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
        self.setup_completion_button()
        self.setup_run_button()
        self.transcription_manager = TranscriptionManager()
        self.transcription_manager.set_callback(self.on_transcription_complete)
        self.completion_manager = CompletionManager()
        self.selected_file_path = None
        self.selected_language_code = None
        self.final_prompt = ""  # Initialize the final_prompt variable

    def setup_title_label(self, title):
        label = ctk.CTkLabel(self, text=title)
        label.pack(pady=10)

    # todo Make it discreet
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
        self.file_frame.pack(padx=10, pady=10)

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
        self.options_frame.pack(padx=10, pady=10)

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
        self,
        prompt_file_path="/Users/Haller/Dev/Python/openai_agi/prompts.json",
    ):
        self.prompt_select_frame = ctk.CTkFrame(self)
        self.prompt_select_frame.pack(padx=10, pady=10)

        self.prompt_select_label = ctk.CTkLabel(
            self.prompt_select_frame, text="Prompt:"
        )
        self.prompt_select_label.pack(side="left", padx=10)

        with open(prompt_file_path, "r") as file:
            prompt_pairs = json.load(file)
        if prompt_pairs is None:
            prompt_pairs = {}  # Ensure it's a dictionary even if load_prompts fails
        self.prompt_menu = ctk.CTkOptionMenu(
            self.prompt_select_frame,
            values=list(prompt_pairs.keys()),
            command=self.update_prompt,
        )
        self.prompt_menu.pack(side="left", padx=10)

        self.prompt_texts = prompt_pairs
        self.selected_prompt_title = None

        # Textbox for displaying and editing prompt text
        self.prompt_textbox = ctk.CTkTextbox(self)
        self.prompt_textbox.pack(padx=10, pady=10, fill="both", expand=True)

        self.save_prompt_button = ctk.CTkButton(
            self.prompt_select_frame,
            text="Save Prompt",
            command=self.save_modified_prompt,
        )
        self.save_prompt_button.pack(side="left", padx=10)

    def update_prompt(self, selected_prompt_title):
        if selected_prompt_title in self.prompt_texts:
            self.selected_prompt_title = selected_prompt_title
            selected_prompt_text = self.prompt_texts[selected_prompt_title]
            self.prompt_textbox.delete("1.0", "end")
            self.prompt_textbox.insert("end", selected_prompt_text)
        else:
            self.prompt_textbox.delete("1.0", "end")
            self.selected_prompt_title = None

    def save_modified_prompt(self):
        if (
            self.selected_prompt_title
            and self.selected_prompt_title in self.prompt_texts
        ):
            modified_prompt_text = self.prompt_textbox.get("1.0", "end-1c")
            self.prompt_texts[self.selected_prompt_title] = modified_prompt_text
            self.final_prompt = modified_prompt_text  # Update the final prompt
            print(f"Saved Modified Prompt: {modified_prompt_text}")  # For demonstration
        else:
            print("No prompt selected or prompt title is invalid.")

    def on_focus_in(self, event):
        if self.prompt_text.get("1.0", "end-1c").strip() == self.placeholder_text:
            self.prompt_text.delete("1.0", "end")

    def on_focus_out(self, event):
        if not self.prompt_text.get("1.0", "end-1c").strip():
            self.prompt_text.insert("end", self.placeholder_text)

    def setup_run_button(self):
        self.run_button = ctk.CTkButton(
            self, text="Run transcription", command=self.start_transcription
        )
        self.run_button.pack(padx=10, pady=20, side="left")

    def setup_process_button(self):
        self.process_button = ctk.CTkButton(
            self, text="Process transcription", command=self.start_completion
        )
        self.process_button.pack(padx=10, pady=20, side="bottom")

    def set_transcription_output_frame(self, transcription_output_frame):
        self.transcription_output_frame = transcription_output_frame

    def start_transcription(self):
        if not self.selected_file_path:
            messagebox.showwarning("Warning", "Please select an input file.")
            return
        if not self.selected_language_code:
            messagebox.showwarning("Warning", "Please select a language.")
            return

        # Use final_prompt for transcription
        final_prompt_text = self.final_prompt if self.final_prompt else ""
        self.transcription_manager.start_transcription(
            self.selected_file_path,
            self.selected_language_code,
            final_prompt_text,
        )

    def start_completion(self):
        # Use final_prompt for transcription
        final_prompt_text = self.final_prompt if self.final_prompt else ""
        self.completion_manager.start_completion()

    def on_transcription_complete(self):
        if hasattr(self, "transcription_output_frame"):
            # Call a method in TranscriptionOutputFrame to update its content
            self.transcription_output_frame.update_transcription_text()

    def start_completion(self):
        transcription_text = self.transcription_output_frame.get_transcription_text()
        prompt_text = self.prompt_textbox.get("1.0", "end-1c")
        combined_input = f"{transcription_text}\n\n{prompt_text}"

        self.completion_manager = CompletionManager()
        self.completion_manager.set_callback(self.on_completion_complete)
        self.completion_manager.start_completion(
            combined_input, "", "gpt-4-1106-preview"
        )

    def on_completion_complete(self):
        # Update the transcription output frame with the completion result
        completion_text = self.completion_manager.completion
        self.transcription_output_frame.update_transcription_text(completion_text)

    def setup_completion_button(self):
        self.completion_button = ctk.CTkButton(
            self, text="Process with AI", command=self.start_completion
        )
        self.completion_button.pack(
            padx=10,
            pady=10,
            side="right",
        )


# Transcription Output Frame Class: ---------------------------------------------------------------------------


class TranscriptionOutputFrame(ctk.CTkFrame):
    def __init__(self, parent, left_panel_instance, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.left_panel_instance = left_panel_instance
        self.setup_title_label("Transcription")
        self.setup_transcription_output_text()
        self.display_transcription()
        self.setup_save_button()

    def setup_title_label(self, title):
        label = ctk.CTkLabel(self, text=title)
        label.pack(pady=10)

    def setup_transcription_output_text(self):
        self.transcription_output_text = ctk.CTkTextbox(self)
        self.transcription_output_text.pack(expand=True, fill="both", padx=10, pady=10)

    def display_transcription(self):
        self.after(1000, self.check_for_transcription)

    def check_for_transcription(self):
        # Check if transcription is complete
        if not self.left_panel_instance.transcription_manager.is_transcribing:
            # If transcription is complete, update the text box
            self.update_transcription_text()
        else:
            # If still transcribing, check again after some time
            self.after(1000, self.check_for_transcription)

    def on_transcription_complete(self):
        # This method can be called by LeftPanelFrame when transcription is complete.
        self.update_transcription_text()

    def update_transcription_text(self, completion=None):
        # Method to update the transcription text box
        self.transcription_output_text.delete("1.0", "end")
        transcription = self.left_panel_instance.transcription_manager.transcription
        if not transcription and not completion:
            self.transcription_output_text.insert("end", "No output available.")
            return
        if transcription:
            self.transcription_output_text.insert("end", transcription)
        if completion:
            self.transcription_output_text.insert("end", completion)

    def setup_save_button(self):
        self.save_button = ctk.CTkButton(
            self, text="Save", command=self.save_transcription
        )
        self.save_button.pack(pady=10)

    def save_transcription(self):
        if not self.left_panel_instance.selected_folder_path:
            messagebox.showwarning("Warning", "No output folder selected.")
            return

        filename = (
            os.path.splitext(
                os.path.basename(self.left_panel_instance.selected_file_path)
            )[0]
            + "_transcription_"
            + datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            + ".txt"
        )
        file_path = os.path.join(
            self.left_panel_instance.selected_folder_path, filename
        )

        with open(file_path, "w", encoding="utf-8") as file:
            transcription_text = self.transcription_output_text.get("1.0", "end-1c")
            file.write(transcription_text)

        messagebox.showinfo("Success", f"File saved successfully in\n{file_path}")

    def get_transcription_text(self):
        return self.transcription_output_text.get("1.0", "end-1c")


# Completion Manager


class CompletionManager:
    def __init__(self):
        self.completion = None
        self.is_completing = False
        self.callback = None

    def set_callback(self, callback):
        """Set a callback function to be called after completion."""
        self.callback = callback

    def start_completion(self, input_text, system_prompt, model="gpt-3.5-turbo"):
        if self.is_completing:
            messagebox.showinfo("Info", "Completion is already in progress.")
            return

        self.is_completing = True
        print("Completion started.")

        # Run completion in a separate thread
        completion_thread = threading.Thread(
            target=self.run_completion,
            args=(input_text, system_prompt, model),
            daemon=True,  # Optional: make this thread a daemon thread
        )
        completion_thread.start()

    def run_completion(self, input_text, system_prompt, model):
        try:
            self.completion = openai_text.openai_completion(
                model,
                input_text,
                system_prompt,
            )
        except Exception as e:
            logging.error(f"Failed to start completion: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start completion: {e}")
            self.completion = "The completion failed."
        finally:
            self.is_completing = False
            print("Completion ended.")
            print(self.completion)
            if self.callback:  # Execute callback in the main thread
                self.callback()


# Transcription Manager


class TranscriptionManager:
    def __init__(self):
        self.transcription = None
        self.is_transcribing = False
        self.callback = None  # Initialize the callback attribute

    def set_callback(self, callback):
        """Set a callback function to be called after transcription."""
        self.callback = callback

    def start_transcription(
        self, selected_file_path, selected_language_code, prompt_text
    ):
        if self.is_transcribing:
            messagebox.showinfo("Info", "Transcription is already in progress.")
            return

        self.is_transcribing = True
        print("Transcription started.")
        transcription_thread = threading.Thread(
            target=self.run_transcription,
            args=(selected_file_path, selected_language_code, prompt_text),
            daemon=True,
        )
        transcription_thread.start()

    def run_transcription(
        self, selected_file_path, selected_language_code, prompt_text
    ):
        try:
            openai_api_key, openai_org = env_utils.load_environment_variables()
            client = openai_audio.init_openai_client(openai_api_key, openai_org)
            if not selected_file_path or not selected_language_code:
                raise ValueError("File path or language code is not set")

            self.transcription = openai_audio.transcribe_audio(
                selected_file_path,
                client,
                selected_language_code,
                prompt_text,
                "text",
            )
        except Exception as e:
            logging.error(f"Failed to start transcription: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to start transcription: {e}")
            self.transcription = "The transcription failed."
        finally:
            self.is_transcribing = False
            if self.callback:
                self.callback()


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
        all_vars_set: bool = env_utils.check_env_variables(mode="gui", parent=self)
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

        self.transcription_output_frame = TranscriptionOutputFrame(
            self, self.left_panel
        )
        self.transcription_output_frame.grid(
            row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10
        )

        self.log_output_frame = LogOutputFrame(self)
        self.log_output_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)

        # Set reference to TranscriptionOutputFrame in LeftPanelFrame
        self.left_panel.set_transcription_output_frame(self.transcription_output_frame)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = AudioTranscriptionApp()
    app.mainloop()
