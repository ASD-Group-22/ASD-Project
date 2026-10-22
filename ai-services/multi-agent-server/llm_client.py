import json
import os
import re
from typing import Any

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
).rstrip("/")

PLANNER_MODEL = os.getenv(
    "MULTI_AGENT_PLANNER_MODEL",
    "qwen2.5:0.5b",
)

WORKER_MODEL = os.getenv(
    "MULTI_AGENT_WORKER_MODEL",
    "qwen2.5:0.5b",
)

REVIEWER_MODEL = os.getenv(
    "MULTI_AGENT_REVIEWER_MODEL",
    "llama3.1:8b",
)

OLLAMA_TIMEOUT_SECONDS = float(
    os.getenv(
        "MULTI_AGENT_OLLAMA_TIMEOUT_SECONDS",
        "300",
    )
)


class LLMClientError(RuntimeError):
    """Raised when the local Ollama service cannot provide a valid response."""


def create_chat_completion(
    messages: list[dict[str, str]],
    *,
    model: str,
    max_tokens: int,
    temperature: float = 0.1,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise LLMClientError(
            f"Ollama request failed: {exc}"
        ) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise LLMClientError(
            "Ollama returned invalid JSON"
        ) from exc

    message = body.get(
        "message"
    )

    if not isinstance(
        message,
        dict,
    ):
        raise LLMClientError(
            "Ollama response did not contain a message object"
        )

    content = message.get(
        "content"
    )

    if not isinstance(
        content,
        str,
    ) or not content.strip():
        raise LLMClientError(
            "Ollama returned an empty model response"
        )

    return content.strip()


def parse_json_object(
    text: str,
) -> dict[str, Any]:
    cleaned = (
        text
        or ""
    ).strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    try:
        value = json.loads(
            cleaned
        )

        if isinstance(
            value,
            dict,
        ):
            return value

    except json.JSONDecodeError:
        pass

    start = cleaned.find(
        "{"
    )
    end = cleaned.rfind(
        "}"
    )

    if start != -1 and end > start:
        try:
            value = json.loads(
                cleaned[start:end + 1]
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned malformed JSON: {cleaned[:300]}"
            ) from exc

        if isinstance(
            value,
            dict,
        ):
            return value

    raise ValueError(
        f"Model did not return a valid JSON object: {cleaned[:300]}"
    )