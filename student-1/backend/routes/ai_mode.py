from flask import Blueprint, jsonify, request
from services import prompt_loader
from services import llm_client
from services import project_service


ai_mode_bp = Blueprint("ai_mode", __name__)


@ai_mode_bp.route("/projects/<int:project_id>/ai/plan", methods=["POST"])
def generate_project_plan(project_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    objective = data.get("objective")

    if not objective:
        return jsonify({
            "error": "Project objective is required"
        }), 400

    try:
        context = project_service.get_project_context(project_id)

        if context is None:
            return jsonify({
                "error": "Project not found"
            }), 404

        system_prompt = prompt_loader.load_prompt(
            "project_plan_system.txt"
        )

        task_prompt = prompt_loader.build_prompt(
            "project_plan_task.txt",
            {
                "PROJECT_ID": project_id,
                "OBJECTIVE": objective,
                "PROJECT": context["project"],
                "TASKS": context["tasks"],
                "MILESTONES": context["milestones"]
            }
        )

        prompt = f"""
{system_prompt}

{task_prompt}
"""

        result = llm_client.generate(prompt)

        return jsonify({
            "project_id": project_id,
            "objective": objective,
            "plan": result
        })

    except Exception as error:
        return jsonify({
            "error": "AI service unavailable",
            "details": str(error)
        }), 503


@ai_mode_bp.route(
    "/projects/<int:project_id>/ai/tasks",
    methods=["POST"]
)
def generate_tasks(project_id):

    data = request.get_json(silent=True) or {}

    objective = data.get(
        "objective",
        "Generate tasks for this project."
    )

    try:

        system_prompt = prompt_loader.load_prompt(
            "task_generation_system.txt"
        )

        task_prompt = prompt_loader.build_prompt(
            "task_generation_task.txt",
            {
                "PROJECT_ID": project_id,
                "OBJECTIVE": objective
            }
        )

        prompt = f"""
{system_prompt}

{task_prompt}
"""

        result = llm_client.generate(prompt)

        return jsonify({
            "project_id": project_id,
            "tasks": result
        })

    except Exception as error:

        return jsonify({
            "error": "AI service unavailable",
            "details": str(error)
        }), 503


@ai_mode_bp.route(
    "/projects/<int:project_id>/ai/assignments",
    methods=["POST"]
)
def recommend_assignments(project_id):

    data = request.get_json(silent=True) or {}

    tasks = data.get("tasks", [])
    members = data.get("members", [])

    try:

        system_prompt = prompt_loader.load_prompt(
            "assignment_system.txt"
        )

        task_prompt = prompt_loader.build_prompt(
            "assignment_task.txt",
            {
                "PROJECT_ID": project_id,
                "TASKS": tasks,
                "MEMBERS": members
            }
        )

        prompt = f"""
{system_prompt}

{task_prompt}
"""

        result = llm_client.generate(prompt)

        return jsonify({
            "project_id": project_id,
            "recommendations": result
        })

    except Exception as error:

        return jsonify({
            "error": "AI service unavailable",
            "details": str(error)
        }), 503


@ai_mode_bp.route(
    "/projects/<int:project_id>/ai/risks",
    methods=["GET"]
)
@ai_mode_bp.route("/projects/<int:project_id>/ai/risks", methods=["GET"])
def analyse_risks(project_id):

    try:
        context = project_service.get_project_context(project_id)

        if context is None:
            return jsonify({
                "error": "Project not found"
            }), 404

        system_prompt = prompt_loader.load_prompt(
            "risk_analysis_system.txt"
        )

        task_prompt = prompt_loader.build_prompt(
            "risk_analysis_task.txt",
            {
                "PROJECT_ID": project_id,
                "PROJECT": context["project"],
                "TASKS": context["tasks"],
                "MILESTONES": context["milestones"]
            }
        )

        prompt = f"""
{system_prompt}

{task_prompt}
"""

        result = llm_client.generate(prompt)

        return jsonify({
            "project_id": project_id,
            "risks": result
        })

    except Exception as error:
        return jsonify({
            "error": "AI service unavailable",
            "details": str(error)
        }), 503