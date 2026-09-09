import json
import os
import requests

from flask import Blueprint, jsonify

from services.llm_client import generate, generate_review
from services.prompt_loader import build_prompt

ai_bp = Blueprint("ai", __name__)

DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://localhost:6001"
)

MAX_ATTEMPTS = 3


def log(message):
    print(f"[AGENTIC LOOP] {message}", flush=True)


def get_project_context(project_id):
    try:
        project = requests.get(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}",
            timeout=5
        )

        tasks = requests.get(
            f"{DATABASE_SERVICE_URL}/projects/{project_id}/tasks",
            timeout=5
        )

        if project.status_code != 200:
            return None

        if tasks.status_code != 200:
            return None

        return {
            "project": project.json(),
            "tasks": tasks.json()
        }

    except requests.RequestException as error:
        log(f"Database error: {error}")
        return None


def generate_suggestion(context, feedback=None):
    prompt = build_prompt(
        "task_generation_system.txt"
    )

    task_prompt = build_prompt(
        "task_generation_task.txt",
        {
            "project": json.dumps(
                context["project"],
                indent=2
            ),
            "tasks": json.dumps(
                context["tasks"],
                indent=2
            )
        }
    )

    if feedback:
        task_prompt += f"""

The previous suggestion was rejected.

REVIEWER FEEDBACK:
{feedback}

Generate a different task that addresses
the reviewer's feedback.

Return only the new task.
"""

    return generate(
        prompt + "\n\n" + task_prompt
    ).strip()


def review_suggestion(suggestion, context):
    log("REVIEWER INPUT")
    log(f"Proposed task: {suggestion}")

    log("Existing tasks:")
    for task in context["tasks"]:
        print(
            f"[AGENTIC LOOP]   - {task['task']}",
            flush=True
        )

    system_prompt = build_prompt(
        "task_review_system.txt"
    )

    review_prompt = f"""
PROJECT:

{json.dumps(context["project"], indent=2)}

EXISTING TASKS:

{json.dumps(context["tasks"], indent=2)}

PROPOSED TASK:

{suggestion}

Compare the proposed task against EVERY existing
task.

Only reject it if it is genuinely the same task
or performs essentially the same action.
"""

    response = generate_review(
        system_prompt + "\n\n" + review_prompt
    )

    try:
        response = response.strip()

        if response.startswith("```"):
            response = (
                response
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        result = json.loads(response)

        return {
            "approved": bool(result.get("approved")),
            "reason": str(
                result.get(
                    "reason",
                    "No reason provided."
                )
            )
        }

    except (json.JSONDecodeError, TypeError):
        return {
            "approved": False,
            "reason": "Reviewer returned invalid JSON."
        }


def run_agentic_loop(project_id):
    log(f"Starting task generation for project {project_id}")

    # OBSERVE
    context = get_project_context(project_id)

    if context is None:
        return {
            "success": False,
            "error": "Project not found or database unavailable."
        }, 404

    log(
        f"OBSERVE: Project = "
        f"{context['project']['name']}"
    )

    log(
        f"OBSERVE: "
        f"{len(context['tasks'])} existing tasks"
    )

    # PLAN
    log(
        "PLAN: Generate one specific, actionable "
        "non-duplicate task."
    )

    feedback = None

    for attempt in range(1, MAX_ATTEMPTS + 1):

        log(f"ATTEMPT {attempt}/{MAX_ATTEMPTS}")

        # ACT
        log("ACT: Generating task with Qwen.")

        try:
            suggestion = generate_suggestion(
                context,
                feedback
            )
        except Exception as error:
            log(f"ACT FAILED: {error}")

            return {
                "success": False,
                "error": "Unable to generate task."
            }, 500

        if not suggestion:
            feedback = "The generated task was empty."
            continue

        log(f"ACT RESULT: {suggestion}")

        # OBSERVE
        log("OBSERVE: Task generated.")

        # REVIEW
        log("REVIEW: Checking task with reviewer.")

        try:
            review = review_suggestion(
                suggestion,
                context
            )
        except Exception as error:
            log(f"REVIEW FAILED: {error}")

            return {
                "success": False,
                "error": "Unable to generate task."
            }, 500

        log(
            f"REVIEW RESULT: "
            f"{review['approved']}"
        )

        log(
            f"REVIEW REASON: "
            f"{review['reason']}"
        )

        # HUMAN REVIEW
        if review["approved"]:
            log(
                "HUMAN REVIEW: "
                "Returning suggestion to frontend."
            )

            log("LOOP COMPLETE")

            return {
                "success": True,
                "suggestion": suggestion
            }, 200

        # ADAPT
        log("ADAPT: Regenerating using reviewer feedback.")

        feedback = review["reason"]

    log("LOOP COMPLETE: Maximum attempts reached.")

    return {
        "success": False,
        "error": "Unable to generate task."
    }, 500


@ai_bp.route(
    "/projects/<int:project_id>/ai/tasks/generate",
    methods=["POST"]
)
def generate_task(project_id):
    try:
        result, status_code = run_agentic_loop(
            project_id
        )

        return jsonify(result), status_code

    except Exception as error:
        log(f"UNEXPECTED ERROR: {error}")

        return jsonify({
            "success": False,
            "error": "Unable to generate task."
        }), 500