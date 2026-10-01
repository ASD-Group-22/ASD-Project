from flask import Blueprint, jsonify, request

from services.mcp_api import (
    get_project,
    get_project_tasks,
    mcp_is_enabled,
    search_project_tasks,
)


mcp_bp = Blueprint(
    "mcp_mode",
    __name__,
)


def _disabled_response():

    return jsonify({
        "status": "disabled",
        "error": "MCP Mode is disabled",
    }), 403


# =========================================================
# MCP STATUS
# =========================================================

@mcp_bp.get("/mcp/status")
def mcp_status():

    return jsonify({
        "status": (
            "enabled"
            if mcp_is_enabled()
            else "disabled"
        ),
        "mcp_enabled": mcp_is_enabled(),
    }), 200


# =========================================================
# PROJECT DETAILS
# =========================================================

@mcp_bp.post("/mcp/project-details")
def mcp_project_details():

    if not mcp_is_enabled():
        return _disabled_response()

    payload = (
        request.get_json(silent=True)
        or request.form
    )

    project_id = str(
        payload.get(
            "project_id",
            "",
        )
    ).strip()

    if not project_id:

        return jsonify({
            "status": "error",
            "error": "project_id is required",
        }), 400

    try:

        result = get_project(
            int(project_id)
        )

        if (
            result.get("status") == "error"
            and result.get("error")
            == "Project not found"
        ):
            return jsonify(result), 404

        status_code = (
            200
            if result.get("status") == "success"
            else 502
        )

        return jsonify(result), status_code

    except (ValueError, TypeError) as exc:

        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 400

    except Exception as exc:

        return jsonify({
            "status": "error",
            "error": f"MCP request failed: {exc}",
        }), 503


# =========================================================
# PROJECT TASKS
# =========================================================

@mcp_bp.post("/mcp/project-tasks")
def mcp_project_tasks():

    if not mcp_is_enabled():
        return _disabled_response()

    payload = (
        request.get_json(silent=True)
        or request.form
    )

    project_id = str(
        payload.get(
            "project_id",
            "",
        )
    ).strip()

    if not project_id:

        return jsonify({
            "status": "error",
            "error": "project_id is required",
        }), 400

    try:

        result = get_project_tasks(
            int(project_id)
        )

        if (
            result.get("status") == "error"
            and result.get("error")
            == "Project not found"
        ):
            return jsonify(result), 404

        status_code = (
            200
            if result.get("status") == "success"
            else 502
        )

        return jsonify(result), status_code

    except (ValueError, TypeError) as exc:

        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 400

    except Exception as exc:

        return jsonify({
            "status": "error",
            "error": f"MCP request failed: {exc}",
        }), 503


# =========================================================
# SEARCH TASKS
# =========================================================

@mcp_bp.post("/mcp/search-tasks")
def mcp_search_tasks():

    if not mcp_is_enabled():
        return _disabled_response()

    payload = (
        request.get_json(silent=True)
        or request.form
    )

    project_id = str(
        payload.get(
            "project_id",
            "",
        )
    ).strip()

    search_term = str(
        payload.get(
            "search_term",
            "",
        )
    ).strip()

    if not project_id:

        return jsonify({
            "status": "error",
            "error": "project_id is required",
        }), 400

    if not search_term:

        return jsonify({
            "status": "error",
            "error": "search_term is required",
        }), 400

    try:

        result = search_project_tasks(
            int(project_id),
            search_term,
        )

        if (
            result.get("status") == "error"
            and result.get("error")
            == "Project not found"
        ):
            return jsonify(result), 404

        status_code = (
            200
            if result.get("status") == "success"
            else 502
        )

        return jsonify(result), status_code

    except (ValueError, TypeError) as exc:

        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 400

    except Exception as exc:

        return jsonify({
            "status": "error",
            "error": f"MCP request failed: {exc}",
        }), 503