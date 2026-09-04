import os
import ollama

# Use host Ollama via env var, default to host.docker.internal
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")

# Explicit client so it actually uses OLLAMA_URL
client = ollama.Client(host=OLLAMA_URL)


def ask_llm(prompt, model="llama3"):
    try:
        response = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
    except Exception as e:
        return f"LLM error: {str(e)}"

