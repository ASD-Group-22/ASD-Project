import os
import requests


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL"
)

OLLAMA_REVIEW_MODEL = os.getenv(
    "OLLAMA_REVIEW_MODEL"
)

OLLAMA_GENERATE_URL = (
    f"{OLLAMA_BASE_URL}/api/generate"
)


def generate(prompt, model=None):
    selected_model = model or OLLAMA_MODEL

    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": selected_model,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]


def generate_review(prompt):
    return generate(
        prompt,
        model=OLLAMA_REVIEW_MODEL
    )