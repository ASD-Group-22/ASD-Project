import os
import requests

from flask import Blueprint, jsonify, request


from flask import Blueprint

projects_bp = Blueprint("projects", __name__)


DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://localhost:6001"
)


@projects_bp.route("/projects", methods=["GET"])
def get_projects():
    try:
        response = requests.get(
            f"{DATABASE_SERVICE_URL}/projects",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@projects_bp.route(
    "/projects/<int:project_id>",
    methods=["GET"]
)
def get_project(project_id):
    try:
        response = requests.get(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@projects_bp.route("/projects", methods=["POST"])
def create_project():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    try:
        response = requests.post(
            f"{DATABASE_SERVICE_URL}/projects",
            json=data,
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@projects_bp.route(
    "/projects/<int:project_id>",
    methods=["PUT"]
)
def update_project(project_id):
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    try:
        response = requests.put(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}",
            json=data,
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503


@projects_bp.route(
    "/projects/<int:project_id>",
    methods=["DELETE"]
)
def delete_project(project_id):
    try:
        response = requests.delete(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}",
            timeout=5
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as error:
        return jsonify({
            "error": "Could not connect to database service",
            "details": str(error)
        }), 503