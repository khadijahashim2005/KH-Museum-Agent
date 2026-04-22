import os
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

def call_llm(prompt: str, model: str = "mistral-small-latest", temperature: float = 0.3) -> str:
    """Call Mistral LLM with a prompt"""
    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content