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
    system_msg = """You are a Python documentation expert. "
        Given a unified diff of code changes, generate or update Google-style docstrings for each modified function. 
        Output only a single JSON object mapping each filename to a valid unified diff patch. 
        Each patch must start with '--- a/{filename}' and '+++ b/{filename}', followed by '@@' hunk headers, then '-' lines for removals and '+' lines for additions.
        Do NOT include any explanations or non-diff text.
        Return ony the JSON object with no initial backticks."""
    
    user_msg = f"""
        Here is the unified diff to process:
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