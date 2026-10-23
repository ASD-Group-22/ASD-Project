
"""
Student 1 adapter for the shared Multi-Agent server.

Student 1 API:
    GET /projects/<project_id>
    GET /projects/<project_id>/tasks

The project endpoint returns a JSON object.
The tasks endpoint returns a JSON array.
"""

import os
from typing import Any

import requests


BACKEND_URL = os.getenv(
    "STUDENT1_BACKEND_URL",
    "http://localhost:5001",
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("STUDENT1_ADAPTER_TIMEOUT_SECONDS", "10")
)

SUPPORTED_TASK_TYPES = {
    "project_overview",
    "project_task_analysis",
    "project_risk_analysis",
}


class Student1AdapterError(RuntimeError):
    """Raised when Student 1 data cannot be retrieved or validated."""


def _get_json(path: str) -> dict[str, Any] | list[Any]:
    """Request a Student 1 endpoint and return a JSON object or array."""
    url = f"{BACKEND_URL}{path}"

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise Student1AdapterError(
            f"Could not reach Student 1 backend at {url}: {exc}"
        ) from exc

    if not response.ok:
        raise Student1AdapterError(
            f"Student 1 backend returned HTTP {response.status_code} "
            f"for {path}: {response.text[:500]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise Student1AdapterError(
            f"Student 1 backend returned invalid JSON for {path}: "
            f"{response.text[:500]}"
        ) from exc

    if not isinstance(payload, (dict, list)):
        raise Student1AdapterError(
            f"Unexpected response from {path}: expected a JSON object "
            f"or array, received {type(payload).__name__}"
        )

    return payload


def _project_id(context: dict[str, Any]) -> int:
    """Extract and validate the project ID from workflow context."""
    if not isinstance(context, dict):
        raise Student1AdapterError(
            "Workflow context must be a JSON object"
        )

    raw_id = context.get("project_id")

    try:
        project_id = int(raw_id)
    except (TypeError, ValueError) as exc:
        raise Student1AdapterError(
            "A valid project_id is required in the workflow context"
        ) from exc

    if project_id <= 0:
        raise Student1AdapterError(
            "project_id must be a positive integer"
        )

    return project_id


def _extract_project(
    payload: dict[str, Any] | list[Any],
) -> dict[str, Any]:
    """Extract a project object from supported response shapes."""
    if not isinstance(payload, dict):
        raise Student1AdapterError(
            "Project endpoint must return a JSON object; "
            f"received {type(payload).__name__}"
        )

    # Actual Student 1 response:
    # {"id": 1, "name": "...", "description": "...", ...}
    if "id" in payload and (
        "name" in payload or "project_id" in payload
    ):
        return payload

    # Also tolerate wrapped API responses.
    project = payload.get("project")
    if isinstance(project, dict):
        return project

    data = payload.get("data")
    if isinstance(data, dict):
        if "project" in data and isinstance(data["project"], dict):
            return data["project"]
        return data

    raise Student1AdapterError(
        "Could not find a project object in the Student 1 response"
    )


def _extract_tasks(
    payload: dict[str, Any] | list[Any],
) -> list[dict[str, Any]]:
    """Extract task records, including a top-level JSON array."""
    # Actual Student 1 response:
    # [{"id": 1, "project_id": 1, "status": "Complete", "task": "..."}]
    if isinstance(payload, list):
        tasks = payload

    elif isinstance(payload, dict):
        tasks = payload.get("tasks")

        if not isinstance(tasks, list):
            data = payload.get("data")

            if isinstance(data, list):
                tasks = data
            elif isinstance(data, dict):
                tasks = data.get("tasks")

    else:
        raise Student1AdapterError(
            "Tasks endpoint must return a JSON array or object"
        )

    if not isinstance(tasks, list):
        raise Student1AdapterError(
            "Could not find a task list in the Student 1 response"
        )

    if not all(isinstance(task, dict) for task in tasks):
        raise Student1AdapterError(
            "Tasks response contains records that are not JSON objects"
        )

    return tasks


def _record_id(record: dict[str, Any]) -> int | None:
    """Return a positive record ID where available."""
    if not isinstance(record, dict):
        return None

    for key in ("id", "project_id", "task_id"):
        raw_id = record.get(key)

        try:
            record_id = int(raw_id)
        except (TypeError, ValueError):
            continue

        if record_id > 0:
            return record_id

    return None


def gather_evidence(
    task_type: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Gather project and task evidence for a Multi-Agent workflow.

    Returns structured evidence for the shared Planner/Worker/Reviewer
    pipeline. This adapter reads data only; it does not modify projects
    or create, update, or delete tasks.
    """
    if task_type not in SUPPORTED_TASK_TYPES:
        raise Student1AdapterError(
            f"Unsupported Student 1 task type: {task_type!r}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_TASK_TYPES))}"
        )

    project_id = _project_id(context)

    project_endpoint = f"/projects/{project_id}"
    tasks_endpoint = f"/projects/{project_id}/tasks"

    project_payload = _get_json(project_endpoint)
    tasks_payload = _get_json(tasks_endpoint)

    project = _extract_project(project_payload)
    tasks = _extract_tasks(tasks_payload)

    # Ensure the returned project matches the requested project.
    returned_project_id = _record_id(project)

    if returned_project_id is not None and returned_project_id != project_id:
        raise Student1AdapterError(
            f"Requested project {project_id}, but the backend returned "
            f"project {returned_project_id}"
        )

    # Ensure task records belong to the requested project.
    # The known Student 1 API includes project_id on each task.
    validated_tasks: list[dict[str, Any]] = []

    for task in tasks:
        task_project_id = task.get("project_id")

        if task_project_id is not None:
            try:
                task_project_id = int(task_project_id)
            except (TypeError, ValueError) as exc:
                raise Student1AdapterError(
                    f"Task {task.get('id', 'unknown')} has an invalid "
                    "project_id"
                ) from exc

            if task_project_id != project_id:
                raise Student1AdapterError(
                    f"Task {task.get('id', 'unknown')} belongs to project "
                    f"{task_project_id}, not requested project {project_id}"
                )

        validated_tasks.append(task)

    evidence_items: list[dict[str, Any]] = [
        {
            "reference_id": f"project:{project_id}",
            "type": "project",
            "data": project,
        }
    ]

    allowed_output_references = [f"project:{project_id}"]
    allowed_task_ids: list[int] = []

    for task in validated_tasks:
        task_id = _record_id(task)

        if task_id is None:
            raise Student1AdapterError(
                "A task record is missing a valid task ID"
            )

        reference_id = f"task:{task_id}"

        evidence_items.append(
            {
                "reference_id": reference_id,
                "type": "task",
                "data": task,
            }
        )

        allowed_task_ids.append(task_id)
        allowed_output_references.append(reference_id)

    return {
        "feature": "student1",
        "task_type": task_type,
        "source": {
            "service": "student-1-backend-api",
            "project_endpoint": project_endpoint,
            "tasks_endpoint": tasks_endpoint,
        },
        "request_context": {
            "project_id": project_id,
        },
        "project": project,
        "tasks": validated_tasks,
        "allowed_project_ids": [project_id],
        "allowed_task_ids": allowed_task_ids,
        "evidence_items": evidence_items,
        "allowed_output_references": allowed_output_references,
        "evidence_count": len(evidence_items),
    }