import ollama

def run_llm(model: str, prompt: str) -> str:
    response = ollama.chat(
        model=model, 
        messages=[{"role": "user", "content": prompt}]
        )
    return response['message']['content']