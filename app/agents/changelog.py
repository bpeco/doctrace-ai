from dotenv import load_dotenv
from groq import Groq
from datetime import date
import os
from openai import OpenAI


load_dotenv()
groq = Groq()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)



def generate_changelog_entry(diff_text):

    today = date.today().isoformat()
    
    prompt = f"""You are a changelog expert.
    Given a unified diff, produce a Keep-a-Changelog formatted entry (date + bullet list) summarizing the changes under the [Unreleased] section.
    Perform the task following these instructions:
    1- Include each change as a bullet starting with the filename in backticks, followed by a colon and a concise summary of **what changed**.
    2- If a hunk consists only of re-formatted lines or whitespace changes, omit it from the changelog.
    3- Only include the files that have been changed, added, or removed. If a file has not been changed, added, or removed, do not include it in the changelog.
    4- No preamble, no explanation, just the entry.

    Here is the actual unified diff on which you need to perform this task:
    ```{diff_text}```
    """

    #chat_completion=groq.chat.completions.create(
    #    model="llama-3.3-70b-versatile",
    #    messages=[
    #        {
    #            "role": "user",
     #           "content": prompt
     #       }
    #   ]
    #)
    completion = client.chat.completions.create(
        model="o4-mini",                # o "gpt-3.5-turbo", según tu cuota
        messages=[{"role": "user", "content": prompt}]
    )

    return completion.choices[0].message.content.strip()
    #return chat_completion.choices[0].message.content.strip()

if __name__ == "__main__":
    print(generate_changelog_entry(
        """diff
@@ -22,4 +22,5 @@ Microservice powered by AI-Agent for automatic generation of Google-style docstr
   git clone https://github.com/<your-username>/doctrace-ai.git
   cd doctrace-ai
 
-_Test commit for diff extraction_
\\ No newline at end of file
+_Test commit for diff extraction_
+_And here is Test Number 2_
\\ No newline at end of file"""))