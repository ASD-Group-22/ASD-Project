from flask import Blueprint, jsonify, request

from services import project_service


normal_ui_bp = Blueprint("normal_ui", __name__)


@normal_ui_bp.route("/projects", methods=["GET"])
def get_projects():
    data, status_code = project_service.get_projects()

    return jsonify(data), status_code


@normal_ui_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    data, status_code = project_service.get_project(project_id)

    return jsonify(data), status_code


@normal_ui_bp.route("/projects", methods=["POST"])
def create_project():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    if not data.get("name"):
        return jsonify({
            "error": "Project name is required"
        }), 400

    if data.get("owner_id") is None:
        return jsonify({
            "error": "owner_id is required"
        }), 400

    result, status_code = project_service.create_project(data)

    return jsonify(result), status_code


@normal_ui_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    result, status_code = project_service.update_project(
        project_id,
        data
    )

    return jsonify(result), status_code


@normal_ui_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):

    result, status_code = project_service.delete_project(
        project_id
    )

    return jsonify(result), status_code