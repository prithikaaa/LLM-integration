import os
from openai import OpenAI
# 1. Initialize the client.
# This automatically reads your API key from the "OPENAI_API_KEY" environment variable.
client = OpenAI()


def ask_llm(
    prompt: str, system_instruction: str = "You are a helpful assistant."
) -> str:
    """Sends a prompt to the OpenAI LLM and returns the text response."""
