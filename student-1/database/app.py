from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Use the Docker volume location.
# Falls back to a local database when running outside Docker.
DATABASE = os.getenv(
    "DATABASE_PATH",
    "/app/data/project_management.db"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    # Enable foreign key support.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "database-service"
    })


# ---------------------------------------------------------
# GET ALL PROJECTS
# ---------------------------------------------------------

@app.route("/projects", methods=["GET"])
def get_projects():

    connection = get_db_connection()

    projects = connection.execute(
        "SELECT * FROM projects ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return jsonify([
        dict(project)
        for project in projects
    ])


# ---------------------------------------------------------
# GET ONE PROJECT
# ---------------------------------------------------------

@app.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):

    connection = get_db_connection()

    project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    connection.close()

    if project is None:
        return jsonify({
            "error": "Project not found"
        }), 404

    return jsonify(dict(project))


# ---------------------------------------------------------
# CREATE PROJECT
# ---------------------------------------------------------

@app.route("/projects", methods=["POST"])
def create_project():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")
    description = data.get("description")
    requirements = data.get("requirements")
    owner_id = data.get("owner_id")
    start_date = data.get("start_date")
    deadline = data.get("deadline")
    status = data.get("status", "Not Started")

    if not name:
        return jsonify({
            "error": "Project name is required"
        }), 400

    if owner_id is None:
        return jsonify({
            "error": "owner_id is required"
        }), 400

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO projects
        (
            name,
            description,
            requirements,
            owner_id,
            start_date,
            deadline,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            description,
            requirements,
            owner_id,
            start_date,
            deadline,
            status
        )
    )

    connection.commit()

    project_id = cursor.lastrowid

    project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    connection.close()

    return jsonify(dict(project)), 201


# ---------------------------------------------------------
# UPDATE PROJECT
# ---------------------------------------------------------

@app.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    connection = get_db_connection()

    existing_project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    if existing_project is None:
        connection.close()

        return jsonify({
            "error": "Project not found"
        }), 404

    # Keep existing values when a field is not supplied.
    name = data.get("name", existing_project["name"])
    description = data.get(
        "description",
        existing_project["description"]
    )
    requirements = data.get(
        "requirements",
        existing_project["requirements"]
    )
    owner_id = data.get(
        "owner_id",
        existing_project["owner_id"]
    )
    start_date = data.get(
        "start_date",
        existing_project["start_date"]
    )
    deadline = data.get(
        "deadline",
        existing_project["deadline"]
    )
    status = data.get(
        "status",
        existing_project["status"]
    )

    connection.execute(
        """
        UPDATE projects
        SET
            name = ?,
            description = ?,
            requirements = ?,
            owner_id = ?,
            start_date = ?,
            deadline = ?,
            status = ?
        WHERE id = ?
        """,
        (
            name,
            description,
            requirements,
            owner_id,
            start_date,
            deadline,
            status,
            project_id
        )
    )

    connection.commit()

    project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    connection.close()

    return jsonify(dict(project))


# ---------------------------------------------------------
# DELETE PROJECT
# ---------------------------------------------------------

@app.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id):

    connection = get_db_connection()

    existing_project = connection.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()

    if existing_project is None:
        connection.close()

        return jsonify({
            "error": "Project not found"
        }), 404

    connection.execute(
        "DELETE FROM projects WHERE id = ?",
        (project_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Project deleted successfully",
        "project_id": project_id
    })

@app.route("/projects/<int:project_id>/tasks", methods=["GET"])
def get_project_tasks(project_id):
    connection = get_db_connection()

    tasks = connection.execute(
        """
        SELECT *
        FROM tasks
        WHERE project_id = ?
        ORDER BY id
        """,
        (project_id,)
    ).fetchall()

    connection.close()

    return jsonify([dict(task) for task in tasks])


@app.route("/projects/<int:project_id>/milestones", methods=["GET"])
def get_project_milestones(project_id):
    connection = get_db_connection()

    milestones = connection.execute(
        """
        SELECT *
        FROM milestones
        WHERE project_id = ?
        ORDER BY id
        """,
        (project_id,)
    ).fetchall()

    connection.close()

    return jsonify([dict(milestone) for milestone in milestones])

# ---------------------------------------------------------
# RUN SERVICE
# ---------------------------------------------------------

if __name__ == "__main__":

    # Make sure the database directory exists.
    database_directory = os.path.dirname(DATABASE)

    if database_directory:
        os.makedirs(
            database_directory,
            exist_ok=True
        )

    app.run(
        host="0.0.0.0",
        port=6001,
        debug=True
    )