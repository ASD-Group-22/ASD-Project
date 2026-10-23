"""Student 5 gateway to the GROUP shared Release 2 Multi-Agent service.

The shared service app.py uses feature=student5, task_type, user_request,
and context. AI services stay disabled by default in cloud environments.
"""
import os
import uuid

import requests
from flask import Blueprint, jsonify, request

bp = Blueprint("release2", __name__)
MULTI_AGENT_SERVER_URL = os.getenv(
    "MULTI_AGENT_SERVER_URL", "http://host.docker.internal:5101"
).rstrip("/")
MULTI_AGENT_MODE = os.getenv("MULTI_AGENT_MODE", "false").lower() == "true"


def relay(method, path, payload=None):
    if not MULTI_AGENT_MODE:
        return jsonify({"status": "disabled", "error": "Multi-Agent disabled in this environment"}), 503
    try:
        response = requests.request(method, MULTI_AGENT_SERVER_URL + path, json=payload, timeout=75)
        return jsonify(response.json()), response.status_code
    except (requests.RequestException, ValueError):
        return jsonify({"status": "unavailable", "error": "Shared Multi-Agent server unavailable"}), 503


@bp.get("/api/multi-agent/health")
def health():
    if not MULTI_AGENT_MODE:
        return jsonify({"status": "disabled", "mode": "multi-agent"})
    return relay("GET", "/health")


@bp.post("/api/multi-agent/workflows")
def start():
    body = request.get_json(silent=True) or {}
    query = body.get("query")
    if not isinstance(query, str) or not 3 <= len(query.strip()) <= 500:
        return jsonify({"error": "query must have 3-500 characters"}), 400
    cleaned = query.strip()
    return relay("POST", "/workflows", {
        "feature": "student5",
        "task_type": "campus_space_recommendation",
        "user_request": cleaned,
        "context": {"query": cleaned},
    })


@bp.get("/api/multi-agent/workflows/<workflow_id>")
def get_workflow(workflow_id):
    try:
        uuid.UUID(workflow_id)
    except ValueError:
        return jsonify({"error": "invalid workflow id"}), 400
    return relay("GET", "/workflows/" + workflow_id)


@bp.post("/api/multi-agent/workflows/<workflow_id>/review")
def review(workflow_id):
    try:
        uuid.UUID(workflow_id)
    except ValueError:
        return jsonify({"error": "invalid workflow id"}), 400
    body = request.get_json(silent=True) or {}
    decision = body.get("decision")
    if decision == "partially_accept":  # compatibility with original Student 5 UI
        decision = "partial_accept"
    if decision not in {"approve", "correct", "partial_accept", "reject"}:
        return jsonify({"error": "invalid decision"}), 400
    notes = body.get("comment") or body.get("notes") or ""
    corrected_response = body.get("corrected_response")

    if decision != "approve" and not str(notes).strip():
        return jsonify({"error": "review notes required for non-approval"}), 400

    if decision == "correct" and not str(corrected_response or "").strip():
        return jsonify({
            "error": "corrected_response is required when decision=correct"
        }), 400

    payload = {
        "decision": decision,
        "notes": str(notes).strip() or None,
    }

    if corrected_response is not None:
        payload["corrected_response"] = str(corrected_response).strip()

    return relay(
        "POST",
        "/workflows/" + workflow_id + "/human-review",
        payload,
    )
