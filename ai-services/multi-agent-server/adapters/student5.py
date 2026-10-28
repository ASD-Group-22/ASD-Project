"""Student 5 evidence adapter for the GROUP shared Multi-Agent coordinator.

Reads stored campus spaces only through Student 5's owning backend API.
Does not perform booking, write to the DB, or claim live availability.
"""
import os
import re
from typing import Any

import requests

from adapters import AdapterError

BACKEND_URL = os.getenv("STUDENT5_BACKEND_URL", "http://127.0.0.1:8055").rstrip("/")
TIMEOUT = float(os.getenv("STUDENT5_ADAPTER_TIMEOUT_SECONDS", "15"))
TASK = "campus_space_recommendation"


def _constraints(text: str) -> dict[str, Any]:
    query = text.lower()
    count = re.search(r"\b(?:for|fits?|seat(?:s|ing)?|capacity\s*(?:of|for)?|group\s*of)\s*(\d{1,3})\s*(?:people|persons|students|seats?)?\b", query)
    if count is None:
        count = re.search(r"\b(\d{1,3})\s*(?:people|persons|students|seats?)\b", query)
    min_capacity = int(count.group(1)) if count else 1
    noise = "quiet" if "quiet" in query else "silent" if "silent" in query else None
    facilities = []
    if "whiteboard" in query:
        facilities.append("whiteboard")
    if re.search(r"\b(power|outlet|charging)\b", query):
        facilities.append("power")
    if re.search(r"\b(wifi|wi-fi|internet)\b", query):
        facilities.append("wifi")
    return {"min_capacity": min_capacity, "noise_level": noise, "facilities": facilities}


def _available_facilities(space: dict[str, Any]) -> str:
    facilities = space.get("facilities") or []
    if isinstance(facilities, str):
        return facilities.lower()
    if isinstance(facilities, list):
        return " ".join(str(item).lower() for item in facilities)
    return ""


def _matches(space: dict[str, Any], constraints: dict[str, Any]) -> bool:
    try:
        capacity = int(space.get("max_capacity") or 0)
    except (TypeError, ValueError):
        capacity = 0
    if capacity < constraints["min_capacity"]:
        return False
    wanted_noise = constraints["noise_level"]
    if wanted_noise and wanted_noise not in str(space.get("noise_level") or "").lower():
        return False
    available = re.sub(r"[^a-z0-9]+", "", _available_facilities(space))
    for facility in constraints["facilities"]:
        variants = {"whiteboard": ["whiteboard"], "power": ["power", "outlet", "charging"], "wifi": ["wifi", "internet"]}[facility]
        if not any(variant in available for variant in variants):
            return False
    return True


def gather_evidence(task_type: str, context: dict[str, Any]) -> dict[str, Any]:
    if task_type != TASK:
        raise AdapterError(f"Student 5 supports task_type={TASK}")
    if not isinstance(context, dict):
        raise AdapterError("Student 5 context must be a JSON object")
    query = context.get("query") or context.get("user_request") or ""
    if not isinstance(query, str) or not query.strip():
        raise AdapterError("Student 5 context.query is required")
    constraints = _constraints(query)
    try:
        response = requests.get(f"{BACKEND_URL}/api/spaces", timeout=TIMEOUT)
        response.raise_for_status()
        spaces = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise AdapterError(f"Cannot retrieve Student 5 stored spaces: {exc}") from exc
    if not isinstance(spaces, list) or any(not isinstance(s, dict) for s in spaces):
        raise AdapterError("Student 5 /api/spaces must return a list of space objects")
    candidates = [s for s in spaces if _matches(s, constraints)]
    evidence_items = []
    for space in candidates:
        sid = space.get("space_id")
        if isinstance(sid, int) and not isinstance(sid, bool):
            evidence_items.append({"reference_id": f"space:{sid}", "kind": "candidate", "data": space})
    references = [e["reference_id"] for e in evidence_items]
    return {
        "feature": "student5",
        "task_type": task_type,
        "source": {"service": "student-5-backend-api", "endpoint": "/api/spaces"},
        "request_context": {"query": query, "constraints": constraints},
        "candidates": [e["data"] for e in evidence_items],
        "allowed_output_references": references,
        "evidence_items": evidence_items,
        "evidence_count": len(evidence_items),
        "total_spaces_checked": len(spaces),
        "notice": "Stored spaces only; no booking or real-time occupancy information.",
    }
