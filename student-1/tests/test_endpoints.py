# ruff: noqa: S101
import os

import requests


BASE_URL = os.getenv("STUDENT1_BACKEND_URL", "http://localhost:5001")


def test_get_projects_endpoint():
    """Release 2 endpoint test 1: retrieve projects."""
    response = requests.get(
        f"{BASE_URL}/projects",
        timeout=10,
    )

    assert response.status_code == 200

    payload = response.json()

    # Support either a direct list or a dictionary containing projects.
    projects = payload if isinstance(payload, list) else payload.get("projects")

    assert isinstance(projects, list)
    assert projects, "Expected at least one project in the database."

    for project in projects:
        assert isinstance(project, dict)
        assert "id" in project


def test_get_project_tasks_endpoint():
    """Release 2 endpoint test 2: retrieve tasks for an existing project."""
    project_id = 1

    project_response = requests.get(
        f"{BASE_URL}/projects/{project_id}",
        timeout=10,
    )

    assert project_response.status_code == 200

    tasks_response = requests.get(
        f"{BASE_URL}/projects/{project_id}/tasks",
        timeout=10,
    )

    assert tasks_response.status_code == 200

    payload = tasks_response.json()
    tasks = payload if isinstance(payload, list) else payload.get("tasks")

    assert isinstance(tasks, list)
    assert tasks, f"Expected seeded tasks for project {project_id}."

    for task in tasks:
        assert isinstance(task, dict)
        assert task.get("project_id") == project_id
        assert "id" in task
        assert task.get("task"), "Each task should have a task description."