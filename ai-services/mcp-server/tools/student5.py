"""Student 5 - AI Campus Space Finder MCP tools.

The tools in this module are intentionally read-only. They obtain feature data
through the Student 5 backend/API and do not open the SQLite database directly.
"""

from __future__ import annotations

import os
from typing import Any

import requests

STUDENT5_BACKEND_URL = os.getenv(
    "STUDENT5_BACKEND_URL", "http://127.0.0.1:8055"
).rstrip("/")


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower()


def _facility_set(space: dict[str, Any]) -> set[str]:
    facilities = space.get("facilities") or []
    if isinstance(facilities, str):
        facilities = [part.strip() for part in facilities.split(",") if part.strip()]
    if not isinstance(facilities, list):
        facilities = [facilities]
    return {_normalise(value) for value in facilities if _normalise(value)}


def _normalise_building(value: Any) -> str:
    text = _normalise(value)
    if text.startswith("building "):
        text = text[len("building "):].strip()
    return text


def _accessible(space: dict[str, Any]) -> bool:
    value = _normalise(space.get("accessibility"))
    return any(token in value for token in ("accessible", "wheelchair", "step-free", "step free"))


def _load_spaces() -> list[dict[str, Any]]:
    response = requests.get(f"{STUDENT5_BACKEND_URL}/api/spaces", timeout=10)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Student 5 backend returned an invalid spaces payload")
    return payload


def register_tools(mcp):
    """Register Student 5's feature-specific read-only MCP tools."""

    @mcp.tool()
    def student5_find_campus_spaces(
        min_capacity: int | None = None,
        building: str | None = None,
        noise_level: str | None = None,
        required_facilities: list[str] | None = None,
        accessible_only: bool = False,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Find real stored Campus Space Finder records matching criteria.

        Boundary: read/filter Student 5 data through the Student 5 backend API.
        This tool cannot write records, run arbitrary SQL, execute shell commands,
        or access another student's database.
        """
        spaces = _load_spaces()
        required = {_normalise(x) for x in (required_facilities or []) if _normalise(x)}
        building_value = _normalise_building(building)
        noise_value = _normalise(noise_level)
        result: list[dict[str, Any]] = []

        for space in spaces:
            try:
                capacity = int(space.get("max_capacity") or 0)
            except (TypeError, ValueError):
                capacity = 0

            if min_capacity is not None and capacity < int(min_capacity):
                continue
            if building_value and building_value != _normalise_building(space.get("building")):
                continue
            if noise_value and noise_value != _normalise(space.get("noise_level")):
                continue
            if required and not required.issubset(_facility_set(space)):
                continue
            if accessible_only and not _accessible(space):
                continue

            result.append(
                {
                    "space_id": space.get("space_id"),
                    "space_name": space.get("space_name"),
                    "building": space.get("building"),
                    "building_level": space.get("building_level"),
                    "room_number": space.get("room_number"),
                    "max_capacity": capacity,
                    "space_type": space.get("space_type"),
                    "noise_level": space.get("noise_level"),
                    "facilities": space.get("facilities") or [],
                    "accessibility": space.get("accessibility"),
                    "image_url": space.get("image_url"),
                    "description": space.get("description"),
                    "opening_time": space.get("opening_time"),
                    "closing_time": space.get("closing_time"),
                }
            )

        safe_limit = max(1, min(int(limit or 5), 10))
        result.sort(key=lambda item: (item["max_capacity"], str(item.get("space_name") or "")))
        return {
            "tool": "student5_find_campus_spaces",
            "feature": "AI Campus Space Finder",
            "count": len(result),
            "matches": result[:safe_limit],
        }

    return None
