"""Student 4 - Skill Profile RAG source integration.

Student 4 owns the feature-specific trusted-data integration in this
module.

The source should:
- retrieve Skill Profile data through the Student 4 backend/API
- convert appropriate feature data into retrieval documents
- include useful source metadata for grounding and citations
- follow the shared RAG source contract
- avoid direct access to another feature's database
"""

import json
import os

import requests


BACKEND_URL = os.getenv(
    "STUDENT4_BACKEND_URL",
    "http://localhost:5005",
).rstrip("/")


def get_documents():
    """Return trusted Student 4 documents for shared RAG ingestion."""
    response = requests.get(
        f"{BACKEND_URL}/api/profiles",
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    # Support a list or an API response containing a "profiles" list.
    profiles = data.get("profiles", []) if isinstance(data, dict) else data

    if not isinstance(profiles, list):
        raise ValueError("Skill Profile API did not return a profile list")

    documents = []

    for profile in profiles:
        if not isinstance(profile, dict):
            continue

        profile_id = profile.get("id", profile.get("profile_id"))
        if profile_id is None:
            continue

        documents.append({
            "content": json.dumps(profile, ensure_ascii=False),
            "source": f"skill-profile:{profile_id}",
            "feature": "student4-skill-profile",
            "metadata": {
                "profile_id": profile_id,
                "source_url": f"{BACKEND_URL}/api/profiles/{profile_id}",
            },
        })

    return documents