import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MODEL = "llama3-8b-8192"  # Use the appropriate model name from GroqCloud

def get_api_key():
    return os.getenv("GROQCLOUD_API_KEY")

def gen(txt):
    try:
        client = Groq(api_key=get_api_key())
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Answer this question\n"
                },
                {
                    "role": "user",
                    "content": txt
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        response_text = ""
        for chunk in completion:
            response_text += chunk.choices[0].delta.content or ""
        
        return response_text
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    print(gen(""))
