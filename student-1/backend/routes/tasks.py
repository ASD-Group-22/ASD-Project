import os
import requests

from flask import Blueprint, jsonify, request


tasks_bp = Blueprint("tasks", __name__)


DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://localhost:6001"
)


@tasks_bp.route(
    "/projects/<int:project_id>/tasks",
    methods=["GET"]
)
def get_project_tasks(project_id):
    try:
        response = requests.get(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@tasks_bp.route(
    "/projects/<int:project_id>/tasks",
    methods=["POST"]
)
def create_task(project_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    try:
        response = requests.post(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
            json=data,
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@tasks_bp.route(
    "/tasks/<int:task_id>",
    methods=["PUT"]
)
def update_task(task_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    try:
        response = requests.put(
            f"{DATABASE_SERVICE_URL}/tasks/{task_id}",
            json=data,
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@tasks_bp.route(
    "/tasks/<int:task_id>",
    methods=["DELETE"]
)
def delete_task(task_id):
    try:
        response = requests.delete(
            f"{DATABASE_SERVICE_URL}/tasks/{task_id}",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503