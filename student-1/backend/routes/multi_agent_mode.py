import requests
from flask import Blueprint, jsonify, request

from services.multi_agent_api import (
    create_project_workflow,
    get_health,
    get_workflow,
    get_workflow_history,
    multi_agent_is_enabled,
    submit_human_review,
)


multi_agent_bp = Blueprint(
    "multi_agent_mode",
    __name__,
)


def request_payload() -> dict:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return request.form.to_dict()


def disabled_response():
    return jsonify({
        "status": "disabled",
        "error": "Multi-Agent Mode is disabled",
    }), 403


def service_error(exc):
    status_code = 503
    if isinstance(exc, requests.HTTPError):
        response = getattr(exc, "response", None)
        if response is not None:
            status_code = (
                response.status_code
                if response.status_code < 500
                else 503
            )

    return jsonify({
        "status": "error",
        "error": str(exc),
    }), status_code


@multi_agent_bp.get("/multi-agent/status")
def multi_agent_status():
    enabled = multi_agent_is_enabled()
    result = {
        "multi_agent_enabled": enabled,
        "status": "enabled" if enabled else "disabled",
        "service_reachable": False,
    }

    if not enabled:
        return jsonify(result), 200

    try:
        health = get_health()
        result["service_reachable"] = health.get("status") == "ok"
        result["service"] = health
    except (requests.RequestException, RuntimeError) as exc:
        result["service_error"] = str(exc)

    return jsonify(result), 200


@multi_agent_bp.post("/multi-agent/workflows")
def multi_agent_create_workflow():
    if not multi_agent_is_enabled():
        return disabled_response()

    payload = request_payload()
    try:
        project_id = int(payload.get("project_id", 0))
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "error": "project_id must be a positive integer",
        }), 400

    if project_id <= 0:
        return jsonify({
            "status": "error",
            "error": "project_id must be a positive integer",
        }), 400

    user_request = str(payload.get("user_request", "")).strip()
    if not user_request:
        user_request = (
            f"Analyse project {project_id}, summarise its tasks, "
            "and identify evidence-backed outstanding work and risks."
        )

    task_type = str(
        payload.get("task_type", "project_task_analysis")
    ).strip()

    try:
        result = create_project_workflow(
            project_id,
            user_request,
            task_type=task_type,
        )
        return jsonify(result), 201
    except ValueError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except (requests.RequestException, RuntimeError) as exc:
        return service_error(exc)


@multi_agent_bp.get("/multi-agent/workflows/<workflow_id>")
def multi_agent_get_workflow(workflow_id):
    if not multi_agent_is_enabled():
        return disabled_response()
    try:
        return jsonify(get_workflow(workflow_id)), 200
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        return service_error(exc)


@multi_agent_bp.get(
    "/multi-agent/workflows/<workflow_id>/history"
)
def multi_agent_get_history(workflow_id):
    if not multi_agent_is_enabled():
        return disabled_response()
    try:
        return jsonify(get_workflow_history(workflow_id)), 200
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        return service_error(exc)


@multi_agent_bp.post(
    "/multi-agent/workflows/<workflow_id>/human-review"
)
def multi_agent_human_review(workflow_id):
    if not multi_agent_is_enabled():
        return disabled_response()

    payload = request_payload()
    decision = str(payload.get("decision", "")).strip()
    if not decision:
        return jsonify({
            "status": "error",
            "error": "decision is required",
        }), 400

    try:
        result = submit_human_review(
            workflow_id,
            decision,
            notes=payload.get("notes"),
            corrected_response=payload.get("corrected_response"),
        )
        return jsonify(result), 200
    except (requests.RequestException, RuntimeError, ValueError) as exc:
        return service_error(exc)
