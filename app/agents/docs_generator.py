from dotenv import load_dotenv
from groq import Groq
from datetime import date
from typing import Dict


load_dotenv()
groq = Groq()

def generate_docstrings(diff_text: str) -> Dict[str, str]:
    system_prompt = f"""You are a docstring expert.
    Take the unified diff, analyze the changes, and generate Google-style docstrings for each modified functions inside each file.
    Perform the task following these instructions:
    1- If a function has been added or modified and has no docstring, generate a docstring for it.
    2- If a function has been modified and has a docstring, update the docstring to reflect the changes in the function.
    3- If a function has been removed, do not generate a docstring for it.
    4- If a function has not been changed, added, or removed, do not generate a docstring for it.
    5- No preamble, no explanation, just return the answer in the following JSON format only: ```{{"filename": <file_path>, "patch": <docstring_patch>"}}```.
    6- Each patch must begin with "*** Begin Patch ***" and end with "*** End Patch ***"."""

    user_prompt = f"""Here is the actual unified diff on which you need to perform this
    task:
    ```{diff_text}```
    """

    chat_completion=groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system", "content": system_prompt},
            {"role":"user", "content": user_prompt}
        ]
    )
    return chat_completion.choices[0].message.content



if __name__ == "__main__":
    pass