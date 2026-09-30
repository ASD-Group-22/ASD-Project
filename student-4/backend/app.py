import os
import requests

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

# These must point to the shared servers' agreed HTTP endpoints.
MCP_TOOL_ENDPOINT = os.getenv("MCP_TOOL_ENDPOINT", "")
RAG_ANSWER_ENDPOINT = os.getenv("RAG_ANSWER_ENDPOINT", "")


@app.route("/api/profiles/<int:profile_id>/mcp", methods=["POST"])
def api_mcp_profile(profile_id):
    if not MCP_TOOL_ENDPOINT:
        return jsonify({"error": "Shared MCP endpoint is not configured"}), 503

    try:
        response = requests.post(
            MCP_TOOL_ENDPOINT,
            json={
                "tool": "student4_get_skill_profile",
                "arguments": {"profile_id": profile_id},
            },
            timeout=30,
        )
        return jsonify(response.json()), response.status_code

    except (requests.RequestException, ValueError):
        return jsonify({"error": "Shared MCP service unavailable"}), 503


@app.route("/api/profiles/<int:profile_id>/rag", methods=["POST"])
def api_rag_profile(profile_id):
    data = request.get_json(silent=True) or {}
    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Question is required"}), 400

    if not RAG_ANSWER_ENDPOINT:
        return jsonify({"error": "Shared RAG endpoint is not configured"}), 503

    try:
        response = requests.post(
            RAG_ANSWER_ENDPOINT,
            json={
                "question": question.strip(),
                "feature": "student4-skill-profile",
                "profile_id": profile_id,
            },
            timeout=90,
        )
        result = response.json()

        if response.ok and not all(
            key in result for key in ("answer", "citations", "confidence")
        ):
            return jsonify({
                "error": "Shared RAG response is missing answer, citations, or confidence"
            }), 502

        return jsonify(result), response.status_code

    except (requests.RequestException, ValueError):
        return jsonify({"error": "Shared RAG service unavailable"}), 503

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5005,
        debug=True
    )
