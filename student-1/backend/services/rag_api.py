import os

import requests


RAG_ENABLED = os.getenv(
    "RAG_ENABLED",
    "true",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL",
    "http://host.docker.internal:5003",
).rstrip("/")


def rag_is_enabled() -> bool:
    return RAG_ENABLED


def _post(
    path: str,
    payload: dict,
) -> dict:

    if not RAG_ENABLED:
        raise RuntimeError(
            "RAG Mode is disabled"
        )

    try:

        response = requests.post(
            f"{RAG_SERVICE_URL}{path}",
            json=payload,
            timeout=(5, 180),
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        raise RuntimeError(
            "Shared RAG service unavailable"
        ) from exc

    try:

        data = response.json()

    except ValueError as exc:

        raise RuntimeError(
            "Shared RAG service returned invalid JSON"
        ) from exc

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Shared RAG response was not an object"
        )

    return data


def refresh_corpus(
    caller: str = "student-1-backend",
) -> dict:

    return _post(
        "/refresh",
        {
            "caller": caller,
        },
    )


def retrieve_context(
    query: str,
    k: int = 5,
    caller: str = "student-1-backend",
) -> dict:

    return _post(
        "/retrieve",
        {
            "query": query,
            "k": k,
            "caller": caller,
        },
    )


def answer_question(
    query: str,
    k: int = 5,
    caller: str = "student-1-backend",
) -> dict:

    return _post(
        "/answer",
        {
            "query": query,
            "k": k,
            "caller": caller,
        },
    )
