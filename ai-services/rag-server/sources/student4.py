"""Student 4 Skill Profile source for the shared RAG pipeline."""

import os

import requests


STUDENT4_BACKEND_URL = os.getenv(
    "STUDENT4_BACKEND_URL", "http://localhost:5005"
).rstrip("/")


def get_documents() -> list[dict]:
    response = requests.get(
        f"{STUDENT4_BACKEND_URL}/api/profiles",
        timeout=15,
    )
    response.raise_for_status()

    profiles = response.json()
    if isinstance(profiles, dict):
        profiles = profiles.get("profiles", [])

    if not isinstance(profiles, list):
        raise ValueError("Student 4 backend returned an invalid profiles list")

    documents = []

    for item in profiles:
        try:
            profile_id = int(item["profile_id"])
        except (KeyError, TypeError, ValueError):
            continue

        # Fetch the full profile so its individual skills are included.
        detail = requests.get(
            f"{STUDENT4_BACKEND_URL}/api/profiles/{profile_id}",
            timeout=15,
        )
        detail.raise_for_status()
        profile = detail.json()

        skill_sentences = []
        for skill in profile.get("skills", []):
            skill_sentences.append(
                f"{skill.get('skill_name', '')} "
                f"(level: {skill.get('skill_level', '')}; "
                f"strength: {skill.get('strength', '')}; "
                f"weakness: {skill.get('weakness', '')})"
            )

        documents.append({
            "chunk_id": f"student4_profile_{profile_id}",
            "source_id": f"student-4:/api/profiles/{profile_id}",
            "feature": "student-4-skill-profile",
            "authority_tier": "tier_1",
            "record_type": "skill_profile",
            "profile_id": profile_id,
            "student_id": profile.get("student_id"),
            "text": (
                f"Skill Profile ID: {profile_id}. "
                f"Student ID: {profile.get('student_id', '')}. "
                f"Skills: {'; '.join(skill_sentences)}."
            ),
        })

    return documents