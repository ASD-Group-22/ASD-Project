import json

from flask import Blueprint, request
import requests

from services.database_api import (
    get_project_by_id_response,
    get_tasks_by_project_response
)


mcp_bp = Blueprint(
    "mcp_mode",
    __name__
)


# ---------------------------------------------------------
# MCP MODE
# ---------------------------------------------------------

def mcp_mode_is_enabled(req) -> bool:

    import os

    enabled = os.getenv(
        "MCP_ENABLED",
        "true"
    ).strip().lower() in (
        "1",
        "true",
        "yes",
        "on"
    )

    if not enabled:
        return False

    mode_header = req.headers.get(
        "X-MCP-Mode",
        "on"
    ).strip().lower()

    return mode_header in (
        "1",
        "true",
        "yes",
        "on"
    )


def mcp_disabled_response():

    return (
        "<p>MCP Mode is disabled.</p>",
        403
    )


def mcp_render_json(title: str, payload):

    return (
        f"<h3>{title}</h3>"
        f"<pre>{json.dumps(payload, indent=2)}</pre>"
    )


# =========================================================
# PROJECT DETAILS
# =========================================================

@mcp_bp.post(
    "/mcp/project-details"
)
def mcp_project_details():

    if not mcp_mode_is_enabled(request):
        return mcp_disabled_response()

    project_id = request.form.get(
        "project_id",
        ""
    ).strip()

    if not project_id:
        return (
            "<p>project_id is required.</p>",
            400
        )

    try:

        response = get_project_by_id_response(
            project_id
        )

        if response.status_code == 404:

            return mcp_render_json(
                "MCP Tool: project_details",
                {
                    "error": "Project not found"
                }
            ), 404

        response.raise_for_status()

        return mcp_render_json(
            "MCP Tool: project_details",
            response.json()
        ), 200

    except requests.RequestException as exc:

        return (
            "<p>MCP project_details failed.</p>"
            f"<pre>{exc}</pre>",
            503
        )


# =========================================================
# PROJECT TASKS
# =========================================================

@mcp_bp.post(
    "/mcp/project-tasks"
)
def mcp_project_tasks():

    if not mcp_mode_is_enabled(request):
        return mcp_disabled_response()

    project_id = request.form.get(
        "project_id",
        ""
    ).strip()

    if not project_id:
        return (
            "<p>project_id is required.</p>",
            400
        )

    try:

        response = get_tasks_by_project_response(
            project_id
        )

        if response.status_code == 404:

            return mcp_render_json(
                "MCP Tool: project_tasks",
                {
                    "error": "Project not found"
                }
            ), 404

        response.raise_for_status()

        return mcp_render_json(
            "MCP Tool: project_tasks",
            response.json()
        ), 200

    except requests.RequestException as exc:

        return (
            "<p>MCP project_tasks failed.</p>"
            f"<pre>{exc}</pre>",
            503
        )


# =========================================================
# SEARCH TASKS
# =========================================================

@mcp_bp.post(
    "/mcp/search-tasks"
)
def mcp_search_tasks():

    if not mcp_mode_is_enabled(request):
        return mcp_disabled_response()

    project_id = request.form.get(
        "project_id",
        ""
    ).strip()

    search_term = request.form.get(
        "search_term",
        ""
    ).strip().lower()

    if not project_id:
        return (
            "<p>project_id is required.</p>",
            400
        )

    if not search_term:
        return (
            "<p>search_term is required.</p>",
            400
        )

    try:

        response = get_tasks_by_project_response(
            project_id
        )

        if response.status_code == 404:

            return mcp_render_json(
                "MCP Tool: search_tasks",
                {
                    "error": "Project not found"
                }
            ), 404

        response.raise_for_status()

        tasks = response.json()

        matching_tasks = [
            task
            for task in tasks
            if search_term in task.get(
                "task",
                ""
            ).lower()
        ]

        return mcp_render_json(
            "MCP Tool: search_tasks",
            matching_tasks
        ), 200

    except requests.RequestException as exc:

        return (
            "<p>MCP search_tasks failed.</p>"
            f"<pre>{exc}</pre>",
            503
        )