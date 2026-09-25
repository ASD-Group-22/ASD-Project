"""Student 1 - Project Management MCP tools.

Student 1 owns the feature-specific MCP tool implementations in this
module.

Tools should:
- expose useful operations for the Project Management feature
- access feature data through the Student 1 backend/API
- return structured responses
- follow the shared MCP tool contracts
- avoid direct access to another feature's database
"""

import os
import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_URL = os.getenv(
    "STUDENT1_BACKEND_URL",
    "http://localhost:5001"
)


def get_project_details(project_id: int):
    if not project_id:
        return {"error": "project_id is required"}

    response = requests.get(
        f"{BACKEND_URL}/projects/{project_id}",
        timeout=5,
    )

    response.raise_for_status()

    project = response.json()

    tasks_response = requests.get(
        f"{BACKEND_URL}/projects/{project_id}/tasks",
        timeout=5,
    )

    tasks_response.raise_for_status()

    tasks = tasks_response.json()

    return {
        "project": project,
        "tasks": tasks,
    }


def get_project_tasks(project_id: int):
    if not project_id:
        return {"error": "project_id is required"}

    response = requests.get(
        f"{BACKEND_URL}/projects/{project_id}/tasks",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()


def search_project_tasks(
    project_id: int,
    search_term: str
):
    term = (search_term or "").strip().lower()

    if not term:
        return {"error": "search_term is required"}

    response = requests.get(
        f"{BACKEND_URL}/projects/{project_id}/tasks",
        timeout=5,
    )

    response.raise_for_status()

    tasks = response.json()

    matches = []

    for task in tasks:
        task_text = str(
            task.get("task", "")
        )

        if term in task_text.lower():
            matches.append(task)

    return matches