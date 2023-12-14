import os

import openai
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
def intitialize_openai():
    load_dotenv()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ORG = os.getenv("OPENAI_ORG")
    openai.api_key = OPENAI_API_KEY

    client = OpenAI(
        organization=OPENAI_ORG,
    )


def initialize_tokenizer(tokenizer_name):
    """
    Initializes and returns a tokenizer.

    :param tokenizer_name: Name of the tokenizer to initialize.
    :return: Initialized tokenizer.
    """

    return tiktoken.get_encoding(tokenizer_name)


def create_chunks(text, chunk_size, tokenizer):
    """
    Yields successive chunk_size-sized chunks from text.

    :param text: The text to be chunked.
    :param chunk_size: The desired size of each chunk.
    :param tokenizer: The tokenizer to use for chunking.
    :return: Yields chunks of text.
    """
    tokens = tokenizer.encode(text)
    i = 0
    while i < len(tokens):
        j = min(i + int(1.5 * chunk_size), len(tokens))
        while j > i + int(0.5 * chunk_size):
            chunk = tokenizer.decode(tokens[i:j])
            if chunk.endswith(".") or chunk.endswith("\n"):
                break
            j -= 1
        if j == i + int(0.5 * chunk_size):
            j = min(i + chunk_size, len(tokens))
        yield tokens[i:j]
        i = j


def openai_completion(model, input_text, system_prompt, format="text", temperature=0):
    """
    Generates a response from OpenAI's API based on the given model, input text, and system prompt.

    :param model: The model to be used for the API call (e.g., 'gpt-3.5-turbo').
    :param input_text: The user input text for the completion.
    :param system_prompt: The system prompt that guides the response generation.
    :param temperature: The temperature setting for the completion (default 0 for deterministic responses).
    :return: The generated text from the API.
    """
    intitialize_openai()
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
        response_format={"type": format},
    )
    return response.choices[0].message.content
