import os
from openai import OpenAI
# 1. Initialize the client.
# This automatically reads your API key from the "OPENAI_API_KEY" environment variable.
client = OpenAI()


def ask_llm(
    prompt: str, system_instruction: str = "You are a helpful assistant."
) -> str:
    """Sends a prompt to the OpenAI LLM and returns the text response."""
try:
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Adjusts creativity (0.0 = deterministic, 1.0 = creative)
            max_tokens=500    # Limits the length of the response
        )
    # Extract and return the text content from the response object
    return response.choices[0].message.content

except Exception as e:
    return f"An error occurred: {e}"
