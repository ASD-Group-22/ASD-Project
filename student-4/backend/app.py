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

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5005,
        debug=True
    )
