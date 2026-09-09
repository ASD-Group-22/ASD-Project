import os
import ollama

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
client = ollama.Client(host=OLLAMA_URL)

def ask_llm(prompt, model="llama3:8b"):
    try:
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"LLM error: {str(e)}"
