import env_utils
import GUI_interface  # Import your module
import openai_audio
import openai_text
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")  # This will be your main page.


# Add more routes here as needed


@app.route("/process", methods=["POST"])
def process():
    user_input = request.form["user_input"]
    # Call your processing functions here, e.g., openai_text.openai_completion
    result = f"Hello {user_input}!"
    print(result)  # Replace with your function
    return render_template("results.html", result=result)  # Show the result


if __name__ == "__main__":
    app.run(debug=True)
