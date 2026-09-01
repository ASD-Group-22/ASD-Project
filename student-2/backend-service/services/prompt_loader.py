from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR.parent
PROMPT_DIR = APP_DIR / "prompts" / "skill_exchange"


def load_prompt(relative_path):
    return (PROMPT_DIR / relative_path).read_text(encoding="utf-8").strip()
