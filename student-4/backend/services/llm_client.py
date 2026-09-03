import json
import os
import requests


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROMPTS_DIR = os.path.join(
    BASE_DIR,
    "prompts"
)


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)


OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:0.5b"
)


def load_prompt(filename):

    path = os.path.join(
        PROMPTS_DIR,
        filename
    )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


def analyse_profile(profile):

    system_prompt = load_prompt(
        "system_prompt.txt"
    )

    context_prompt = load_prompt(
        "context_prompt.txt"
    )

    analysis_prompt = load_prompt(
        "analysis_prompt.txt"
    )


    profile_context = json.dumps(
        profile,
        indent=2
    )


    prompt = f"""
{context_prompt}

STUDENT PROFILE DATA:

{profile_context}

{analysis_prompt}
"""


    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "system": system_prompt,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2
            }
        },
        timeout=90
    )


    response.raise_for_status()


    result = response.json()

    ai_text = result.get(
        "response",
        ""
    )


    if not ai_text:
        raise ValueError(
            "Ollama returned an empty response"
        )


    analysis = json.loads(ai_text)


    return {
        "summary": analysis.get(
            "summary",
            ""
        ),

        "strengths": analysis.get(
            "strengths",
            []
        ),

        "weaknesses": analysis.get(
            "weaknesses",
            []
        ),

        "recommendations": analysis.get(
            "recommendations",
            []
        )
    }