"""Supply Skill Profile evidence to the shared Multi-Agent workflow."""

import os

import requests


BACKEND_URL = os.getenv(
    "STUDENT4_BACKEND_URL",
    "http://localhost:5005",
).rstrip("/")


def gather_evidence(task_type: str, context: dict) -> dict:
    if task_type != "skill_profile_review":
        raise ValueError(
            "Student 4 supports task_type=skill_profile_review"
        )

    profile_id = context.get("profile_id")

    if (
        isinstance(profile_id, bool)
        or not isinstance(profile_id, int)
        or profile_id <= 0
    ):
        raise ValueError(
            "context.profile_id must be a positive integer"
        )

    endpoint = f"/api/profiles/{profile_id}"

    try:
        response = requests.get(
            f"{BACKEND_URL}{endpoint}",
            timeout=15,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            "Student 4 backend is unavailable"
        ) from exc

    if response.status_code == 404:
        raise ValueError("Skill profile not found")

    if not response.ok:
        raise RuntimeError(
            f"Student 4 backend returned HTTP {response.status_code}"
        )

    try:
        profile = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Student 4 backend returned invalid JSON"
        ) from exc

    if not isinstance(profile, dict):
        raise ValueError("Expected a profile object")

    skills = profile.get("skills")

    if not isinstance(skills, list) or not skills:
        raise ValueError("Profile has no skills to review")

    if not all(isinstance(skill, dict) for skill in skills):
        raise ValueError("Profile contains invalid skill records")

    reference = f"profile:{profile_id}"

    return {
        "feature": "student4",
        "task_type": task_type,
        "source": {
            "service": "student-4-backend-api",
            "endpoint": endpoint,
        },
        "request_context": {
            "profile_id": profile_id,
        },
        "evidence_items": [
            {
                "reference_id": reference,
                "kind": "skill_profile",
                "data": profile,
            }
        ],
        "allowed_output_references": [reference],
        "evidence_count": 1,
    }