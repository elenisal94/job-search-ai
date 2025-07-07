import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_openai():
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Tell me something about pirates"}]
    )
    print(response.choices[0].message.content)

test_openai()
