import os
from tkinter import messagebox

from dotenv import dotenv_values, load_dotenv


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


def load_environment_variables():
    check_env_variables()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_org = os.getenv("OPENAI_ORG")
    return openai_api_key, openai_org


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
