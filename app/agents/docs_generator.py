from dotenv import load_dotenv
from groq import Groq
from typing import Dict
import json

load_dotenv()
groq = Groq()

def generate_docstrings(diff_text: str) -> Dict[str, str]:
    """
    Generates unified diff patches for Google-style docstrings for each modified function
    based on the provided unified diff. Returns a dict mapping file paths
    to unified diff patch strings.
    """
    system_msg = """ "You are a Python documentation expert.\n"
    "Given a unified diff of code changes, generate or update Google-style docstrings\n"
    "for each modified function. Output ONE valid JSON object where:\n"
    "- Keys are file paths.\n"
    "- Values are unified-diff patches as a single-line JSON string, with all newlines escaped as \"\\\\n\" and all internal quotes escaped.\n"
    "Each patch must start with \"--- a/{filename}\\n+++ b/{filename}\" etc.\n"
    "Do NOT output any other text, explanations, or markdown bullets.\n"
    "No preamble, no initial backticks.\n"
    "Example output:\n"
    "{\n"
    "  \"app/main.py\": \"--- a/app/main.py\\\\n+++ b/app/main.py\\\\n@@ -10,3 +10,7 @@ ...\",\n"
    "  \"utils/get_utils.py\": \"--- a/utils/get_utils.py\\\\n+++ b/utils/get_utils.py\\\\n@@ -1,1 +1,5 ...\"\n"
    "}"""
    
    user_msg = f"""
        Process the following unified diff:
        ```diff
        {diff_text}
        ```"""

    chat = groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
        ],
    )
    raw = chat.choices[0].message.content.strip()
    try:
        patches = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from doc generator: {e}\nRaw response: {raw}")
    if not isinstance(patches, dict):
        raise RuntimeError(f"Expected JSON object, got: {type(patches)}\nRaw response: {raw}")
    return patches

if __name__ == "__main__":
    sample_diff = """@@ -10,3 +10,7 @@ def foo(bar):
     pass"""
    print(generate_docstrings(sample_diff))