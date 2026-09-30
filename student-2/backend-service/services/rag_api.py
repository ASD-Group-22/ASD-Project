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

RAG_TIMEOUT_SECONDS = int(
    os.getenv(
        "RAG_TIMEOUT_SECONDS",
        "180",
    )
)


def rag_is_enabled() -> bool:
    return RAG_ENABLED


def call_rag(
    path: str,
    payload: dict,
) -> dict:
    if not RAG_ENABLED:
        raise RuntimeError(
            "RAG Mode is disabled"
        )

    response = requests.post(
        f"{RAG_SERVICE_URL}{path}",
        json=payload,
        timeout=RAG_TIMEOUT_SECONDS,
    )

    try:
        data = response.json()
    except ValueError:
        response.raise_for_status()

        raise RuntimeError(
            "RAG server returned "
            "a non-JSON response"
        )

    if response.status_code >= 400:
        raise requests.HTTPError(
            (
                f"RAG service {path} failed "
                f"with HTTP "
                f"{response.status_code}: "
                f"{data}"
            ),
            response=response,
        )

    return data


def refresh_corpus() -> dict:
    return call_rag(
        "/refresh",
        {
            "caller": (
                "student-2-backend"
            ),
        },
    )


def retrieve_context(
    query: str,
    k: int = 5,
) -> dict:
    return call_rag(
        "/retrieve",
        {
            "query": query,
            "k": k,
            "caller": (
                "student-2-backend"
            ),
        },
    )


def answer_question(
    query: str,
    k: int = 5,
) -> dict:
    return call_rag(
        "/answer",
        {
            "query": query,
            "k": k,
            "caller": (
                "student-2-backend"
            ),
        },
    )