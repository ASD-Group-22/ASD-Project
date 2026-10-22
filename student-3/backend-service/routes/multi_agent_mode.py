import requests
from flask import Blueprint, jsonify, request
from services import multi_agent_api


multi_agent_bp = Blueprint("multi_agent", __name__)


def _disabled():
    return jsonify(status="disabled", error="Multi-Agent Mode is disabled"), 403


def _error(exc):
    status = 503
    if isinstance(exc, requests.HTTPError) and exc.response is not None and exc.response.status_code < 500:
        status = exc.response.status_code
    return jsonify(status="error", error=str(exc)), status


def _payload():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@multi_agent_bp.get("/multi-agent/status")
def status():
    result = {"multi_agent_enabled": multi_agent_api.is_enabled(), "service_reachable": False}
    if not result["multi_agent_enabled"]:
        return jsonify({**result, "status": "disabled"})
    try:
        service = multi_agent_api.health()
        return jsonify({**result, "status": "enabled", "service_reachable": service.get("status") == "ok", "service": service})
    except (requests.RequestException, RuntimeError) as exc:
        return jsonify({**result, "status": "enabled", "service_error": str(exc)})


@multi_agent_bp.post("/multi-agent/workflows")
def create_workflow():
    if not multi_agent_api.is_enabled():
        return _disabled()
    data = _payload()
    subject = data.get("subject")
    group_size = data.get("group_size", 5)
    student_ids = data.get("student_ids")
    if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 100:
        return jsonify(status="error", error="subject must contain 1 to 100 characters"), 400
    if type(group_size) is not int or not 3 <= group_size <= 5:
        return jsonify(status="error", error="group_size must be an integer from 3 to 5"), 400
    if not isinstance(student_ids, list) or not student_ids or any(type(item) is not int or item <= 0 for item in student_ids):
        return jsonify(status="error", error="student_ids must be a nonempty list of positive integer IDs"), 400
    if len(student_ids) != len(set(student_ids)):
        return jsonify(status="error", error="student_ids cannot contain duplicates"), 400
    user_request = str(data.get("user_request") or "").strip()
    if not user_request:
        user_request = f"Recommend balanced groups for {subject.strip()} using the selected evidence."
    user_request += (
        " Use the recorded subject skill requirements and selected skill profiles. "
        "Student IDs only identify profiles; never calculate, average or rank IDs. "
        "Explain skill coverage and any unavoidable gaps."
    )
    try:
        return jsonify(multi_agent_api.create_group_workflow(subject.strip(), group_size, student_ids, user_request)), 201
    except (requests.RequestException, RuntimeError) as exc:
        return _error(exc)


@multi_agent_bp.get("/multi-agent/workflows/<workflow_id>")
def workflow(workflow_id):
    if not multi_agent_api.is_enabled():
        return _disabled()
    try:
        return jsonify(multi_agent_api.get_workflow(workflow_id))
    except (requests.RequestException, RuntimeError) as exc:
        return _error(exc)


@multi_agent_bp.get("/multi-agent/workflows/<workflow_id>/history")
def history(workflow_id):
    if not multi_agent_api.is_enabled():
        return _disabled()
    try:
        return jsonify(multi_agent_api.get_history(workflow_id))
    except (requests.RequestException, RuntimeError) as exc:
        return _error(exc)


@multi_agent_bp.post("/multi-agent/workflows/<workflow_id>/human-review")
def human_review(workflow_id):
    if not multi_agent_api.is_enabled():
        return _disabled()
    data = _payload()
    decision = str(data.get("decision") or "").strip()
    if decision not in {"approve", "correct", "partial_accept", "reject"}:
        return jsonify(status="error", error="decision must be approve, correct, partial_accept, or reject"), 400
    try:
        return jsonify(multi_agent_api.submit_human_review(workflow_id, decision, data.get("notes"), data.get("corrected_response")))
    except (requests.RequestException, RuntimeError) as exc:
        return _error(exc)
