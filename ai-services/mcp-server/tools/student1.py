"""
Student 1 - Project Management MCP tools.

These tools are registered with the shared Release 1 MCP server.

The MCP server does not access the Student 1 database directly.
Instead, the tools call the Student 1 backend API.
"""

import os

import requests


STUDENT1_BACKEND_URL = os.getenv(
    "STUDENT1_BACKEND_URL",
    "http://localhost:5001",
).rstrip("/")


REQUEST_TIMEOUT_SECONDS = float(
    os.getenv(
        "STUDENT1_MCP_TIMEOUT_SECONDS",
        "5",
    )
)


# =========================================================
# PROJECT DETAILS
# =========================================================

def _project_details(
    project_id: int,
    caller: str = "student-1",
) -> dict:

    try:
        parsed_project_id = int(project_id)

        if parsed_project_id <= 0:
            raise ValueError(
                "project_id must be a positive integer"
            )

    except (TypeError, ValueError) as exc:

        return {
            "status": "error",
            "tool": "project_details",
            "caller": caller,
            "error": str(exc),
        }

    try:

        response = requests.get(
            (
                f"{STUDENT1_BACKEND_URL}"
                f"/projects/{parsed_project_id}"
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:

            return {
                "status": "error",
                "tool": "project_details",
                "caller": caller,
                "project_id": parsed_project_id,
                "error": "Project not found",
            }

        response.raise_for_status()

        project = response.json()

        return {
            "status": "success",
            "tool": "project_details",
            "caller": caller,
            "project": project,
        }

    except (
        requests.RequestException,
        ValueError,
    ) as exc:

        return {
            "status": "error",
            "tool": "project_details",
            "caller": caller,
            "project_id": parsed_project_id,
            "error": str(exc),
        }


# =========================================================
# PROJECT TASKS
# =========================================================

def _project_tasks(
    project_id: int,
    caller: str = "student-1",
) -> dict:

    try:
        parsed_project_id = int(project_id)

        if parsed_project_id <= 0:
            raise ValueError(
                "project_id must be a positive integer"
            )

    except (TypeError, ValueError) as exc:

        return {
            "status": "error",
            "tool": "project_tasks",
            "caller": caller,
            "error": str(exc),
        }

    try:

        response = requests.get(
            (
                f"{STUDENT1_BACKEND_URL}"
                f"/projects/{parsed_project_id}/tasks"
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:

            return {
                "status": "error",
                "tool": "project_tasks",
                "caller": caller,
                "project_id": parsed_project_id,
                "error": "Project not found",
            }

        response.raise_for_status()

        tasks = response.json()

        return {
            "status": "success",
            "tool": "project_tasks",
            "caller": caller,
            "project_id": parsed_project_id,
            "task_count": len(tasks),
            "tasks": tasks,
        }

    except (
        requests.RequestException,
        ValueError,
    ) as exc:

        return {
            "status": "error",
            "tool": "project_tasks",
            "caller": caller,
            "project_id": parsed_project_id,
            "error": str(exc),
        }


# =========================================================
# SEARCH TASKS
# =========================================================

def _search_tasks(
    project_id: int,
    search_term: str,
    caller: str = "student-1",
) -> dict:

    try:
        parsed_project_id = int(project_id)

        if parsed_project_id <= 0:
            raise ValueError(
                "project_id must be a positive integer"
            )

    except (TypeError, ValueError) as exc:

        return {
            "status": "error",
            "tool": "search_tasks",
            "caller": caller,
            "error": str(exc),
        }

    search_term = str(
        search_term or ""
    ).strip().lower()

    if not search_term:

        return {
            "status": "error",
            "tool": "search_tasks",
            "caller": caller,
            "project_id": parsed_project_id,
            "error": "search_term is required",
        }

    try:

        response = requests.get(
            (
                f"{STUDENT1_BACKEND_URL}"
                f"/projects/{parsed_project_id}/tasks"
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:

            return {
                "status": "error",
                "tool": "search_tasks",
                "caller": caller,
                "project_id": parsed_project_id,
                "error": "Project not found",
            }

        response.raise_for_status()

        tasks = response.json()

        matching_tasks = [
            task
            for task in tasks
            if search_term in str(
                task.get("task", "")
            ).lower()
        ]

        return {
            "status": "success",
            "tool": "search_tasks",
            "caller": caller,
            "project_id": parsed_project_id,
            "search_term": search_term,
            "result_count": len(matching_tasks),
            "tasks": matching_tasks,
        }

    except (
        requests.RequestException,
        ValueError,
    ) as exc:

        return {
            "status": "error",
            "tool": "search_tasks",
            "caller": caller,
            "project_id": parsed_project_id,
            "search_term": search_term,
            "error": str(exc),
        }


# =========================================================
# REGISTER MCP TOOLS
# =========================================================

def register_tools(mcp):

    @mcp.tool()
    def project_details(
        project_id: int,
        caller: str = "student-1",
    ) -> dict:

        return _project_details(
            project_id=project_id,
            caller=caller,
        )

    @mcp.tool()
    def project_tasks(
        project_id: int,
        caller: str = "student-1",
    ) -> dict:

        return _project_tasks(
            project_id=project_id,
            caller=caller,
        )

    @mcp.tool()
    def search_tasks(
        project_id: int,
        search_term: str,
        caller: str = "student-1",
    ) -> dict:

        return _search_tasks(
            project_id=project_id,
            search_term=search_term,
            caller=caller,
        )

    return None