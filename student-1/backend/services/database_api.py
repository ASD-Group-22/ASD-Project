import os

import requests


DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://database-service:6001"
)


# =========================================================
# PROJECTS
# =========================================================

def get_projects():

    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects",
        timeout=5
    )

    response.raise_for_status()

    return response.json()


def get_project_by_id_response(project_id):

    return requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}",
        timeout=5
    )


# =========================================================
# TASKS
# =========================================================

def get_tasks_by_project_response(project_id):

    return requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
        timeout=5
    )


def get_project_tasks(project_id):

    response = get_tasks_by_project_response(
        project_id
    )

    response.raise_for_status()

    return response.json()