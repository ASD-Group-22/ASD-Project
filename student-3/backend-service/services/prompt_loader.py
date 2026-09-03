import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROMPT_ROOT = os.path.join(PROJECT_ROOT, "prompts", "group_service", "implementation")

def load_prompt(name: str) -> str:
    path = os.path.join(PROMPT_ROOT, f"{name}.txt")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
