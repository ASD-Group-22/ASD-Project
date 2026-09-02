import os
import requests


DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://localhost:6001"
)


def get_projects():

    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects",
        timeout=5
    )

    return response.json(), response.status_code


def get_project(project_id):

    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}",
        timeout=5
    )

    return response.json(), response.status_code


def create_project(data):

    response = requests.post(
        f"{DATABASE_SERVICE_URL}/projects",
        json=data,
        timeout=5
    )

    return response.json(), response.status_code


def update_project(project_id, data):

    response = requests.put(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}",
        json=data,
        timeout=5
    )

    return response.json(), response.status_code


def delete_project(project_id):

    response = requests.delete(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}",
        timeout=5
    )

    return response.json(), response.status_code

def get_project_tasks(project_id):
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
        timeout=5
    )
    return response.json(), response.status_code


def get_project_milestones(project_id):
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}/milestones",
        timeout=5
    )
    return response.json(), response.status_code

def get_project_context(project_id):
    project_response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}",
        timeout=5
    )

    tasks_response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
        timeout=5
    )

    milestones_response = requests.get(
        f"{DATABASE_SERVICE_URL}/projects/{project_id}/milestones",
        timeout=5
    )

    if project_response.status_code != 200:
        return None

    return {
        "project": project_response.json(),
        "tasks": tasks_response.json(),
        "milestones": milestones_response.json()
    }