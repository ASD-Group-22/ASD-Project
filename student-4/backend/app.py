import os
import requests

from services.mcp_api import get_profile_via_mcp
from services.llm_client import analyse_profile
from flask import Flask, request, jsonify
from services.database_api import (
    create_profile,
    get_profile,
    get_profile_by_student_id,
    update_profile,
    delete_profile
)


app = Flask(__name__)


# HEALTH CHECK
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Skill Profile Backend Service",
        "status": "running"
    })


# CREATE PROFILE
@app.route("/api/profiles", methods=["POST"])
def api_create_profile():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    result, status_code = create_profile(data)

    return jsonify(result), status_code


# GET PROFILE
@app.route("/api/profiles/<int:profile_id>", methods=["GET"])
def api_get_profile(profile_id):

    result, status_code = get_profile(profile_id)

    return jsonify(result), status_code


# UPDATE PROFILE
@app.route("/api/profiles/<int:profile_id>", methods=["PUT"])
def api_update_profile(profile_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    result, status_code = update_profile(
        profile_id,
        data
    )

    return jsonify(result), status_code


# DELETE PROFILE
@app.route("/api/profiles/<int:profile_id>", methods=["DELETE"])
def api_delete_profile(profile_id):

    result, status_code = delete_profile(profile_id)

    return jsonify(result), status_code

# GET PROFILE BY STUDENT ID
@app.route("/api/profiles/student/<int:student_id>", methods=["GET"])
def api_get_profile_by_student_id(student_id):

    result, status_code = get_profile_by_student_id(student_id)

    return jsonify(result), status_code

# ADDED FOR STUDENT 3 TO LIST ALL PROFILES
@app.get('/api/profiles')
def api_list_profiles():
    import requests
    from services.database_api import list_profiles
    try:
        result, status_code = list_profiles()
        return jsonify(result), status_code
    except (requests.RequestException, ValueError):
        return jsonify({"error": 'Skill profile database service unavailable'}), 503

# GENERATE AI PROFILE ANALYSIS
@app.route(
    "/api/profiles/<int:profile_id>/analyse",
    methods=["POST"]
)
def api_analyse_profile(profile_id):
    if os.getenv(
        "AI_ENABLED",
        "true",
    ).lower() in (
        "false",
        "0",
        "no",
    ):
        return jsonify({
            "error": "AI Mode is disabled"
        }), 503

    profile, status_code = get_profile(
        profile_id
    )

    if status_code != 200:
        return jsonify(profile), status_code


    if not profile.get("skills"):
        return jsonify({
            "error": "Profile has no skills to analyse"
        }), 400


    try:

        analysis = analyse_profile(
            profile
        )

        return jsonify({
            "profile_id": profile_id,
            "analysis": analysis
        }), 200


    except Exception as error:

        return jsonify({
            "error": "AI analysis failed",
            "details": str(error)
        }), 503

RAG_ANSWER_ENDPOINT = os.getenv(
    "RAG_ANSWER_ENDPOINT",
    "http://host.docker.internal:5003/answer",
)


@app.route("/api/profiles/<int:profile_id>/mcp", methods=["POST"])
def api_mcp_profile(profile_id):
    try:
        result = get_profile_via_mcp(profile_id)
        return jsonify(result), 200
    except Exception:
        app.logger.exception("Skill Profile MCP request failed")
        return jsonify({"error": "Shared MCP service unavailable"}), 503


@app.route("/api/profiles/<int:profile_id>/rag", methods=["POST"])
def api_rag_profile(profile_id):
    if os.getenv(
        "RAG_ENABLED",
        "true",
    ).lower() in (
        "false",
        "0",
        "no",
    ):
        return jsonify({
            "error": "RAG Mode is disabled"
        }), 503

    data = request.get_json(silent=True) or {}
    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Question is required"}), 400

    try:
        response = requests.post(
            RAG_ANSWER_ENDPOINT,
            json={
                "query": (
                    f"Skill Profile ID {profile_id}. "
                    f"{question.strip()}"
                ),
                "k": 5,
                "caller": "student-4-backend",
            },
            timeout=90,
        )
        result = response.json()
        return jsonify(result), response.status_code

    except (requests.RequestException, ValueError):
        return jsonify({"error": "Shared RAG service unavailable"}), 503

# RELEASE 2: MULTI-AGENT SKILL PROFILE REVIEW

MULTI_AGENT_URL = os.getenv(
    "MULTI_AGENT_URL",
    "http://host.docker.internal:5101",
).rstrip("/")


def multi_agent_enabled():
    return os.getenv(
        "MULTI_AGENT_ENABLED", "false"
    ).lower() in ("true", "1", "yes")


def multi_agent_request(method, path, payload=None):
    try:
        response = requests.request(
            method,
            f"{MULTI_AGENT_URL}{path}",
            json=payload,
            timeout=300,
        )
        result = response.json()

        if not isinstance(result, dict):
            raise ValueError("Expected a JSON object")

        return result, response.status_code

    except requests.Timeout:
        return {
            "error": (
                "Multi-Agent request timed out. "
                "The workflow may still be running."
            )
        }, 504

    except (requests.RequestException, ValueError):
        app.logger.exception("Multi-Agent request failed")
        return {"error": "Shared Multi-Agent service unavailable"}, 503


@app.post("/api/profiles/<int:profile_id>/multi-agent")
def api_start_profile_workflow(profile_id):
    if not multi_agent_enabled():
        return jsonify({"error": "Multi-Agent mode is disabled"}), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    user_request = data.get("user_request", "")
    if not isinstance(user_request, str) or not user_request.strip():
        return jsonify({"error": "A review request is required"}), 400

    try:
        profile, status_code = get_profile(profile_id)
    except (requests.RequestException, ValueError):
        return jsonify({"error": "Profile database unavailable"}), 503

    if status_code != 200:
        return jsonify(profile), status_code

    if not profile.get("skills"):
        return jsonify({"error": "Profile has no skills to review"}), 400

    result, status_code = multi_agent_request(
        "POST",
        "/workflows",
        {
            "feature": "student4",
            "task_type": "skill_profile_review",
            "user_request": user_request.strip(),
            "context": {"profile_id": profile_id},
        },
    )
    return jsonify(result), status_code


@app.get("/api/multi-agent/workflows/<uuid:workflow_id>")
def api_get_profile_workflow(workflow_id):
    if not multi_agent_enabled():
        return jsonify({"error": "Multi-Agent mode is disabled"}), 503

    result, status_code = multi_agent_request(
        "GET", f"/workflows/{workflow_id}"
    )

    if status_code == 200 and result.get("feature") != "student4":
        return jsonify({"error": "Student 4 workflow not found"}), 404

    return jsonify(result), status_code


@app.post("/api/multi-agent/workflows/<uuid:workflow_id>/human-review")
def api_review_profile_workflow(workflow_id):
    if not multi_agent_enabled():
        return jsonify({"error": "Multi-Agent mode is disabled"}), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    decision = data.get("decision")
    if not isinstance(decision, str) or decision not in (
        "approve", "correct", "partial_accept", "reject"
    ):
        return jsonify({"error": "Invalid review decision"}), 400

    notes = data.get("notes", "")
    corrected_response = data.get("corrected_response", "")

    if not isinstance(notes, str) or not isinstance(corrected_response, str):
        return jsonify({"error": "Review notes and correction must be text"}), 400

    if decision == "correct" and not corrected_response.strip():
        return jsonify({"error": "Enter a corrected response"}), 400

    workflow, status_code = multi_agent_request(
        "GET", f"/workflows/{workflow_id}"
    )

    if status_code != 200:
        return jsonify(workflow), status_code

    if workflow.get("feature") != "student4":
        return jsonify({"error": "Student 4 workflow not found"}), 404

    result, status_code = multi_agent_request(
        "POST",
        f"/workflows/{workflow_id}/human-review",
        {
            "decision": decision,
            "notes": notes.strip(),
            "corrected_response": corrected_response.strip(),
        },
    )
    return jsonify(result), status_code

if __name__ == "__main__":

    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),  # noqa: S104 - required for container ingress
        port=5005,
        debug=os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    )
