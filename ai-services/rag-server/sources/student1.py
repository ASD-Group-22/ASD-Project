"""Student 1 - Project Management RAG source integration.

Student 1 owns the feature-specific trusted-data integration in this
module.

The source should:
- retrieve Project Management data through the Student 1 backend/API
- convert appropriate feature data into retrieval documents
- include useful source metadata for grounding and citations
- follow the shared RAG source contract
- avoid direct access to another feature's database
"""


import os
from datetime import datetime, timezone

import requests


DATABASE_SERVICE_URL = os.getenv(
    "STUDENT1_DATABASE_SERVICE_URL",
    "http://localhost:6001"
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def build_project_chunks():
    chunks = []

    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects",
        timeout=10
    )

    response.raise_for_status()

    projects = response.json()

    for project in projects:

        project_id = project.get("id")

        chunks.append({
            "chunk_id": f"student1_project_{project_id}",
            "source_id": (
                f"student1:database-service:/projects/{project_id}"
            ),
            "authority_tier": "tier_1",
            "text": (
                f"Student 1 project record: "
                f"project_id={project.get('id')}, "
                f"name={project.get('name')}, "
                f"description={project.get('description')}, "
                f"start_date={project.get('start_date')}, "
                f"end_date={project.get('end_date')}, "
                f"status={project.get('status')}."
            ),
            "metadata": {
                "source_type": "database_service",
                "student": "student1",
                "table": "projects",
                "project_id": project_id
            },
            "indexed_at": now_iso()
        })

    return chunks


def build_task_chunks():
    chunks = []

    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects",
        timeout=10
    )

    response.raise_for_status()

    projects = response.json()

    for project in projects:

        project_id = project.get("id")

        task_response = requests.get(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
            timeout=10
        )

        if task_response.status_code == 404:
            continue

        task_response.raise_for_status()

        tasks = task_response.json()

        for task in tasks:

            task_id = task.get("id")

            chunks.append({
                "chunk_id": f"student1_task_{task_id}",
                "source_id": (
                    f"student1:database-service:"
                    f"/projects/{project_id}/tasks"
                ),
                "authority_tier": "tier_1",
                "text": (
                    f"Student 1 task record: "
                    f"task_id={task.get('id')}, "
                    f"project_id={task.get('project_id')}, "
                    f"project_name={project.get('name')}, "
                    f"task={task.get('task')}, "
                    f"status={task.get('status')}."
                ),
                "metadata": {
                    "source_type": "database_service",
                    "student": "student1",
                    "table": "tasks",
                    "project_id": project_id,
                    "task_id": task_id
                },
                "indexed_at": now_iso()
            })

    return chunks


def build_chunks():
    chunks = []

    try:
        chunks.extend(
            build_project_chunks()
        )

        chunks.extend(
            build_task_chunks()
        )

        return {
            "status": "success",
            "student": "student1",
            "chunks": chunks
        }

    except requests.RequestException as exc:

        return {
            "status": "error",
            "student": "student1",
            "error": str(exc),
            "chunks": []
        }