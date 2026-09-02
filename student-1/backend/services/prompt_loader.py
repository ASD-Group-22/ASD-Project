from pathlib import Path


PROMPT_DIR = (
    Path(__file__).resolve().parent.parent
    / "prompts"
)


def load_prompt(filename):
    prompt_path = PROMPT_DIR / filename

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}"
        )

    return prompt_path.read_text(
        encoding="utf-8"
    ).strip()


def build_prompt(filename, variables=None):

    prompt = load_prompt(filename)

    if variables:

        for key, value in variables.items():

            placeholder = "{{" + key + "}}"

            prompt = prompt.replace(
                placeholder,
                str(value)
            )

    return prompt