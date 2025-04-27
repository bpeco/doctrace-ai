from dotenv import load_dotenv
from groq import Groq
from datetime import date


load_dotenv()
groq = Groq()



def generate_changelog_entry(diff_text):

    today = date.today().isoformat()
    
    prompt = f"""You are a changelog expert.
    Given a unified diff, produce a Keep-a-Changelog formatted entry (date + bullet list) summarizing the changes under the [Unreleased] section.
    If a hunk consists only of re-formatted lines or whitespace changes, omit it from the changelog.
    No preamble, no explanation, just the entry.
    
    Output format:

    ```
    ## {today}
    - **file_1**: <bullet point summary>
    - **file_1**: <bullet point summary>
    - **file_2**: <bullet point summary>
    - **file_3**: <bullet point summary>
    
    
    Here is the actual unified diff on which you need to perform this task:
    ```{diff_text}```
    """

    chat_completion=groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return chat_completion.choices[0].message.content.strip()

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