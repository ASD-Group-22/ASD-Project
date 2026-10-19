import os

import requests


MULTI_AGENT_ENABLED = os.getenv(
    "MULTI_AGENT_ENABLED",
    "true",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

MULTI_AGENT_SERVICE_URL = os.getenv(
    "MULTI_AGENT_SERVICE_URL",
    "http://host.docker.internal:5101",
).rstrip("/")

MULTI_AGENT_TIMEOUT_SECONDS = int(
    os.getenv(
        "MULTI_AGENT_TIMEOUT_SECONDS",
        "240",
    )
)


def multi_agent_is_enabled() -> bool:
    return MULTI_AGENT_ENABLED


def _request(
    method: str,
    path: str,
    payload: dict | None = None,
) -> dict:
    if not MULTI_AGENT_ENABLED:
        raise RuntimeError(
            "Multi-Agent Mode is disabled"
        )

    response = requests.request(
        method=method,
        url=f"{MULTI_AGENT_SERVICE_URL}{path}",
        json=payload,
        timeout=MULTI_AGENT_TIMEOUT_SECONDS,
    )

    try:
        data = response.json()
    except ValueError:
        response.raise_for_status()

        raise RuntimeError(
            "Multi-Agent server returned a non-JSON response"
        )

    if response.status_code >= 400:
        raise requests.HTTPError(
            (
                f"Multi-Agent service {path} failed "
                f"with HTTP {response.status_code}: {data}"
            ),
            response=response,
        )

    if not isinstance(
        data,
        dict,
    ):
        raise RuntimeError(
            "Multi-Agent server returned an unexpected response shape"
        )

    return data


def get_health() -> dict:
    return _request(
        "GET",
        "/health",
    )


def create_skill_exchange_workflow(
    listing_id: int,
    user_request: str,
) -> dict:
    listing_id = int(
        listing_id
    )

    if listing_id <= 0:
        raise ValueError(
            "listing_id must be a positive integer"
        )

    user_request = str(
        user_request or ""
    ).strip()

    if not user_request:
        raise ValueError(
            "user_request is required"
        )

    return _request(
        "POST",
        "/workflows",
        {
            "feature": "student2",
            "task_type": "skill_exchange_match",
            "user_request": user_request,
            "context": {
                "listing_id": listing_id,
            },
        },
    )


def get_workflow(
    workflow_id: str,
) -> dict:
    workflow_id = str(
        workflow_id or ""
    ).strip()

    if not workflow_id:
        raise ValueError(
            "workflow_id is required"
        )

    return _request(
        "GET",
        f"/workflows/{workflow_id}",
    )


def get_workflow_history(
    workflow_id: str,
) -> dict:
    workflow_id = str(
        workflow_id or ""
    ).strip()

    if not workflow_id:
        raise ValueError(
            "workflow_id is required"
        )

    return _request(
        "GET",
        f"/workflows/{workflow_id}/history",
    )


def submit_human_review(
    workflow_id: str,
    decision: str,
    notes: str | None = None,
    corrected_response: str | None = None,
) -> dict:
    workflow_id = str(
        workflow_id or ""
    ).strip()

    if not workflow_id:
        raise ValueError(
            "workflow_id is required"
        )

    payload = {
        "decision": str(
            decision or ""
        ).strip(),
        "notes": notes,
        "corrected_response": corrected_response,
    }

    return _request(
        "POST",
        f"/workflows/{workflow_id}/human-review",
        payload,
    )