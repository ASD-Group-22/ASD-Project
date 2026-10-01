"""Student 5 - AI Campus Space Finder trusted RAG source adapter.

Student 5 owns this file. It converts Student 5 feature/API data into the shared
RAG document contract. It does not implement retrieval or generation logic.
"""

from __future__ import annotations

import os
from typing import Any

import requests

STUDENT5_BACKEND_URL = os.getenv(
    "STUDENT5_BACKEND_URL", "http://127.0.0.1:8055"
).rstrip("/")

FEATURE_ID = "student-5"
FEATURE_NAME = "AI Campus Space Finder"


def _overview_document() -> dict[str, Any]:
    return {
        "source_id": "student5-feature-overview",
        "source": "Student 5 Campus Space Finder feature contract",
        "feature_id": FEATURE_ID,
        "student": 5,
        "feature": FEATURE_NAME,
        "title": "Campus Space Finder purpose and boundaries",
        "content": (
            "The AI Campus Space Finder helps students identify suitable campus spaces "
            "from real stored records using requirements such as capacity, noise level, "
            "facilities, building preference and accessibility. The feature does not "
            "provide login or booking functionality and does not claim live occupancy "
            "or live room availability. The frontend communicates with the Student 5 "
            "backend/API. The backend accesses campus-space data through the Student 5 "
            "database service API and validates recommendations against stored records."
        ),
    }


def _space_document(space: dict[str, Any]) -> dict[str, Any]:
    facilities = space.get("facilities") or []
    if isinstance(facilities, list):
        facilities_text = ", ".join(str(value) for value in facilities)
    else:
        facilities_text = str(facilities)

    source_id = f"campus-space-{space.get('space_id')}"
    content = (
        f"Campus space: {space.get('space_name')}. "
        f"Building: {space.get('building')}. "
        f"Level: {space.get('building_level')}. "
        f"Room: {space.get('room_number')}. "
        f"Maximum capacity: {space.get('max_capacity')}. "
        f"Space type: {space.get('space_type')}. "
        f"Noise level: {space.get('noise_level')}. "
        f"Facilities: {facilities_text}. "
        f"Accessibility: {space.get('accessibility')}. "
        f"Opening time: {space.get('opening_time')}. "
        f"Closing time: {space.get('closing_time')}. "
        f"Description: {space.get('description') or ''}"
    )
    return {
        "source_id": source_id,
        "source": f"Student 5 backend /api/spaces record {space.get('space_id')}",
        "feature_id": FEATURE_ID,
        "student": 5,
        "feature": FEATURE_NAME,
        "title": str(space.get("space_name") or source_id),
        "content": content,
    }


def get_documents() -> list[dict[str, Any]]:
    """Return trusted Student 5 documents for the shared RAG pipeline."""
    documents = [_overview_document()]
    response = requests.get(f"{STUDENT5_BACKEND_URL}/api/spaces", timeout=10)
    response.raise_for_status()
    spaces = response.json()
    if not isinstance(spaces, list):
        raise ValueError("Student 5 backend returned an invalid spaces payload")
    documents.extend(_space_document(space) for space in spaces)
    return documents
