import os
from typing import Any

import requests


BACKEND_URL = os.getenv(
    "STUDENT2_BACKEND_URL",
    "http://localhost:5202",
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv(
        "STUDENT2_ADAPTER_TIMEOUT_SECONDS",
        "10",
    )
)


class Student2AdapterError(RuntimeError):
    """Raised when Student 2 evidence cannot be retrieved safely."""


def _get_json(path: str) -> dict[str, Any]:
    url = f"{BACKEND_URL}{path}"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise Student2AdapterError(
            f"Student 2 backend request failed: {exc}"
        ) from exc

    if not response.ok:
        try:
            body = response.json()
        except ValueError:
            body = {
                "error": response.text.strip()
            }

        raise Student2AdapterError(
            f"Student 2 backend returned HTTP "
            f"{response.status_code}: {body}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise Student2AdapterError(
            "Student 2 backend returned invalid JSON"
        ) from exc

    if not isinstance(payload, dict):
        raise Student2AdapterError(
            "Student 2 backend returned an unexpected response shape"
        )

    return payload


def _listing_id(context: dict[str, Any]) -> int:
    try:
        listing_id = int(
            context.get("listing_id")
        )
    except (TypeError, ValueError) as exc:
        raise Student2AdapterError(
            "context.listing_id must be a positive integer"
        ) from exc

    if listing_id <= 0:
        raise Student2AdapterError(
            "context.listing_id must be a positive integer"
        )

    return listing_id


def gather_evidence(
    task_type: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    if task_type != "skill_exchange_match":
        raise Student2AdapterError(
            "Student 2 currently supports only "
            "task_type=skill_exchange_match"
        )

    listing_id = _listing_id(
        context
    )

    endpoint = (
        f"/skill-exchange/{listing_id}/matches"
    )

    payload = _get_json(
        endpoint
    )

    listing = payload.get(
        "listing"
    )
    candidates = payload.get(
        "candidates"
    )

    if not isinstance(listing, dict):
        raise Student2AdapterError(
            "Matching endpoint did not return requester listing evidence"
        )

    if not isinstance(candidates, list):
        raise Student2AdapterError(
            "Matching endpoint did not return candidate evidence"
        )

    allowed_listing_ids = []

    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise Student2AdapterError(
                "Candidate evidence contains an invalid record"
            )

        candidate_id = candidate.get(
            "listing_id"
        )

        if isinstance(candidate_id, int):
            allowed_listing_ids.append(
                candidate_id
            )

    evidence_items = [
        {
            "reference_id": f"listing:{listing_id}",
            "kind": "requester",
            "data": listing,
        }
    ]

    for candidate in candidates:
        evidence_items.append(
            {
                "reference_id": f"listing:{candidate['listing_id']}",
                "kind": "candidate",
                "data": candidate,
            }
        )

    allowed_output_references = [
        f"listing:{candidate_id}"
        for candidate_id in allowed_listing_ids
    ]

    return {
        "feature": "student2",
        "task_type": task_type,
        "source": {
            "service": "student-2-backend-api",
            "endpoint": endpoint,
        },
        "request_context": {
            "listing_id": listing_id,
        },
        "requester": listing,
        "candidates": candidates,
        "allowed_listing_ids": allowed_listing_ids,
        "evidence_items": evidence_items,
        "allowed_output_references": allowed_output_references,
        "evidence_count": len(evidence_items),
    }