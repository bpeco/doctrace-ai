from dotenv import load_dotenv
from groq import Groq
from typing import Dict
import json
import base64

load_dotenv()
groq = Groq()

def generate_docstrings(diff_text: str) -> Dict[str, str]:
    """
    Generates Google-style docstring patches for each modified function
    based on the provided unified diff. Returns a dict mapping file paths
    to unified-diff patch strings with actual newlines.
    """
    # System message: instructions and JSON format
    system_msg = (
        "You are a Python documentation expert. "
        "Given a unified diff of code changes, generate or update Google-style docstrings for each modified function only. "
        "Output ONE valid JSON object mapping filenames to Base64-encoded unified diff patches. "
        "Do NOT include any explanations or extra text. "
        "Example output format: {\"app/main.py\": \"<Base64 string>\"}"
    )
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
        encoded_map = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from doc generator: {e}\nRaw response: {raw}")
    if not isinstance(encoded_map, dict):
        raise RuntimeError(f"Expected JSON object mapping filenames to Base64 strings, got: {type(encoded_map)}")

    # Decode Base64 patches into actual diff text
    patches: Dict[str, str] = {}
    for file_path, b64_patch in encoded_map.items():
        try:
            diff_bytes = base64.b64decode(b64_patch)
            patches[file_path] = diff_bytes.decode('utf-8')
        except Exception as e:
            raise RuntimeError(f"Failed to Base64-decode patch for {file_path}: {e}")
    return patches

if __name__ == "__main__":
    sample_diff = "@@ -1 +1 @@\n-# old\n+# new"
    print(generate_docstrings(sample_diff))
