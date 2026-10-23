import os

import requests


ENABLED = os.getenv("MULTI_AGENT_ENABLED", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
SERVICE_URL = os.getenv(
    "MULTI_AGENT_SERVICE_URL",
    "http://host.docker.internal:5101",
).rstrip("/")
TIMEOUT_SECONDS = int(os.getenv("MULTI_AGENT_TIMEOUT_SECONDS", "240"))


def is_enabled():
    return ENABLED


def _request(method, path, payload=None):
    if not ENABLED:
        raise RuntimeError("Multi-Agent Mode is disabled")

    response = requests.request(
        method,
        f"{SERVICE_URL}{path}",
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )

    try:
        data = response.json()
    except ValueError:
        response.raise_for_status()
        raise RuntimeError("Multi-Agent server returned non-JSON data")

    if response.status_code >= 400:
        raise requests.HTTPError(
            f"Multi-Agent service {path} failed with HTTP {response.status_code}: {data}",
            response=response,
        )
    if not isinstance(data, dict):
        raise RuntimeError("Multi-Agent server returned an invalid response")
    return data


def health():
    return _request("GET", "/health")


def create_group_workflow(subject, group_size, student_ids, user_request):
    return _request("POST", "/workflows", {
        "feature": "student3",
        "task_type": "group_formation_recommendation",
        "user_request": user_request,
        "context": {
            "subject": subject,
            "group_size": group_size,
            "student_ids": student_ids,
        },
    })


def get_workflow(workflow_id):
    return _request("GET", f"/workflows/{workflow_id}")


def get_history(workflow_id):
    return _request("GET", f"/workflows/{workflow_id}/history")


def submit_human_review(workflow_id, decision, notes=None, corrected_response=None):
    return _request("POST", f"/workflows/{workflow_id}/human-review", {
        "decision": decision,
        "notes": notes,
        "corrected_response": corrected_response,
    })
