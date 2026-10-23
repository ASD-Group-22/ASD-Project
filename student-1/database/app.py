import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)

CORS(app)


DATABASE_PATH = "/app/data/project_management.db"


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "healthy",
        "service": "database-service"
    })


# =========================================================
# PROJECTS
# =========================================================

# ---------------------------------------------------------
# GET ALL PROJECTS
# ---------------------------------------------------------

@app.route(
    "/projects",
    methods=["GET"]
)
def get_projects():

    connection = get_db_connection()

    projects = connection.execute(
        """
        SELECT
            id,
            name,
            description,
            start_date,
            end_date,
            status
        FROM projects
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return jsonify([
        dict(project)
        for project in projects
    ])


# ---------------------------------------------------------
# GET ONE PROJECT
# ---------------------------------------------------------

@app.route(
    "/projects/<int:project_id>",
    methods=["GET"]
)
def get_project(project_id):

    connection = get_db_connection()

    project = connection.execute(
        """
        SELECT
            id,
            name,
            description,
            start_date,
            end_date,
            status
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    connection.close()

    if project is None:

        return jsonify({
            "error": "Project not found"
        }), 404

    return jsonify(
        dict(project)
    )


# ---------------------------------------------------------
# CREATE PROJECT
# ---------------------------------------------------------

@app.route(
    "/projects",
    methods=["POST"]
)
def create_project():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name")

    if not name:

        return jsonify({
            "error": "Project name is required"
        }), 400

    description = data.get(
        "description",
        ""
    )

    start_date = data.get(
        "start_date"
    )

    end_date = data.get(
        "end_date"
    )

    status = data.get(
        "status",
        "Not Started"
    )

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO projects (
            name,
            description,
            start_date,
            end_date,
            status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            name,
            description,
            start_date,
            end_date,
            status
        )
    )

    connection.commit()

    project_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "id": project_id,
        "name": name,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "status": status
    }), 201


# ---------------------------------------------------------
# UPDATE PROJECT
# ---------------------------------------------------------

@app.route(
    "/projects/<int:project_id>",
    methods=["PUT"]
)
def update_project(project_id):

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    allowed_fields = {
        "name",
        "description",
        "start_date",
        "end_date",
        "status"
    }

    updates = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    if not updates:

        return jsonify({
            "error": "No valid fields provided"
        }), 400

    connection = get_db_connection()

    existing_project = connection.execute(
        """
        SELECT id
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if existing_project is None:

        connection.close()

        return jsonify({
            "error": "Project not found"
        }), 404

    set_clause = ", ".join(
        f"{field} = ?"
        for field in updates
    )

    values = list(
        updates.values()
    )

    values.append(project_id)

    query = f"UPDATE projects SET {set_clause} WHERE id = ?"  # noqa: S608 - columns restricted to allowed_fields
    connection.execute(query, values)

    connection.commit()

    project = connection.execute(
        """
        SELECT
            id,
            name,
            description,
            start_date,
            end_date,
            status
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    connection.close()

    return jsonify(
        dict(project)
    )


# ---------------------------------------------------------
# DELETE PROJECT
# ---------------------------------------------------------

@app.route(
    "/projects/<int:project_id>",
    methods=["DELETE"]
)
def delete_project(project_id):

    connection = get_db_connection()

    project = connection.execute(
        """
        SELECT id
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:

        connection.close()

        return jsonify({
            "error": "Project not found"
        }), 404

    connection.execute(
        """
        DELETE FROM projects
        WHERE id = ?
        """,
        (project_id,)
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Project deleted successfully"
    })


# =========================================================
# TASKS
# =========================================================

# ---------------------------------------------------------
# GET PROJECT TASKS
# ---------------------------------------------------------

@app.route(
    "/projects/<int:project_id>/tasks",
    methods=["GET"]
)
def get_project_tasks(project_id):

    connection = get_db_connection()

    project = connection.execute(
        """
        SELECT id
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:

        connection.close()

        return jsonify({
            "error": "Project not found"
        }), 404

    tasks = connection.execute(
        """
        SELECT
            id,
            project_id,
            task,
            status
        FROM tasks
        WHERE project_id = ?
        ORDER BY id ASC
        """,
        (project_id,)
    ).fetchall()

    connection.close()

    return jsonify([
        dict(task)
        for task in tasks
    ])


# ---------------------------------------------------------
# CREATE TASK
# ---------------------------------------------------------

@app.route(
    "/projects/<int:project_id>/tasks",
    methods=["POST"]
)
def create_task(project_id):

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    task = data.get("task")

    if not task:

        return jsonify({
            "error": "Task is required"
        }), 400

    status = data.get(
        "status",
        "Pending"
    )

    connection = get_db_connection()

    project = connection.execute(
        """
        SELECT id
        FROM projects
        WHERE id = ?
        """,
        (project_id,)
    ).fetchone()

    if project is None:

        connection.close()

        return jsonify({
            "error": "Project not found"
        }), 404

    cursor = connection.execute(
        """
        INSERT INTO tasks (
            project_id,
            task,
            status
        )
        VALUES (?, ?, ?)
        """,
        (
            project_id,
            task,
            status
        )
    )

    connection.commit()

    task_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "id": task_id,
        "project_id": project_id,
        "task": task,
        "status": status
    }), 201


# ---------------------------------------------------------
# UPDATE TASK
# ---------------------------------------------------------

@app.route(
    "/tasks/<int:task_id>",
    methods=["PUT"]
)
def update_task(task_id):

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "Request body is required"
        }), 400

    allowed_fields = {
        "task",
        "status"
    }

    updates = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    if not updates:

        return jsonify({
            "error": "No valid fields provided"
        }), 400

    connection = get_db_connection()

    existing_task = connection.execute(
        """
        SELECT id
        FROM tasks
        WHERE id = ?
        """,
        (task_id,)
    ).fetchone()

    if existing_task is None:

        connection.close()

        return jsonify({
            "error": "Task not found"
        }), 404

    set_clause = ", ".join(
        f"{field} = ?"
        for field in updates
    )

    values = list(
        updates.values()
    )

    values.append(task_id)

    query = f"UPDATE tasks SET {set_clause} WHERE id = ?"  # noqa: S608 - columns restricted to allowed_fields
    connection.execute(query, values)

    connection.commit()

    task = connection.execute(
        """
        SELECT
            id,
            project_id,
            task,
            status
        FROM tasks
        WHERE id = ?
        """,
        (task_id,)
    ).fetchone()

    connection.close()

    return jsonify(
        dict(task)
    )


# ---------------------------------------------------------
# DELETE TASK
# ---------------------------------------------------------

@app.route(
    "/tasks/<int:task_id>",
    methods=["DELETE"]
)
def delete_task(task_id):

    connection = get_db_connection()

    task = connection.execute(
        """
        SELECT id
        FROM tasks
        WHERE id = ?
        """,
        (task_id,)
    ).fetchone()

    if task is None:

        connection.close()

        return jsonify({
            "error": "Task not found"
        }), 404

    connection.execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,)
    )

    connection.commit()

    connection.close()

    return jsonify({
        "message": "Task deleted successfully"
    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",  # noqa: S104 - required for Docker networking
        port=6001,
        debug=False
    )