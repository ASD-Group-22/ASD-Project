from flask import Flask, render_template, request, jsonify
import os
import requests


app = Flask(__name__)


BACKEND_SERVICE_URL = os.getenv(
    "BACKEND_SERVICE_URL",
    "http://localhost:5005"
)


@app.route("/", methods=["GET"])
def index():

    return render_template("index.html")


# CREATE PROFILE
@app.route("/profiles", methods=["POST"])
def create_profile():

    data = request.get_json()

    try:
        response = requests.post(
            f"{BACKEND_SERVICE_URL}/api/profiles",
            json=data,
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "Backend service unavailable"
        }), 503


# GET PROFILE
@app.route("/profiles/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):

    try:
        response = requests.get(
            f"{BACKEND_SERVICE_URL}/api/profiles/{profile_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "Backend service unavailable"
        }), 503


# UPDATE PROFILE
@app.route("/profiles/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id):

    data = request.get_json()

    try:
        response = requests.put(
            f"{BACKEND_SERVICE_URL}/api/profiles/{profile_id}",
            json=data,
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "Backend service unavailable"
        }), 503


# DELETE PROFILE
@app.route("/profiles/<int:profile_id>", methods=["DELETE"])
def delete_profile(profile_id):

    try:
        response = requests.delete(
            f"{BACKEND_SERVICE_URL}/api/profiles/{profile_id}",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "Backend service unavailable"
        }), 503

# GENERATE AI ANALYSIS
@app.route("/profiles/<int:profile_id>/analyse", methods=["POST"])
def analyse_profile(profile_id):

    try:
        response = requests.post(
            f"{BACKEND_SERVICE_URL}/api/profiles/{profile_id}/analyse",
            timeout=90
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({
            "error": "AI service unavailable"
        }), 503

# MCP SKILL PROFILE TOOL
@app.route("/profiles/<int:profile_id>/mcp", methods=["POST"])
def mcp_profile(profile_id):
    try:
        response = requests.post(
            f"{BACKEND_SERVICE_URL}/api/profiles/{profile_id}/mcp",
            timeout=30,
        )
        return jsonify(response.json()), response.status_code

    except (requests.RequestException, ValueError):
        return jsonify({"error": "MCP backend request failed"}), 503


# RAG SKILL PROFILE QUESTION
@app.route("/profiles/<int:profile_id>/rag", methods=["POST"])
def rag_profile(profile_id):
    data = request.get_json(silent=True) or {}
    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Question is required"}), 400

    try:
        response = requests.post(
            f"{BACKEND_SERVICE_URL}/api/profiles/{profile_id}/rag",
            json={"question": question.strip()},
            timeout=90,
        )
        return jsonify(response.json()), response.status_code

    except (requests.RequestException, ValueError):
        return jsonify({"error": "RAG backend request failed"}), 503

# RELEASE 2: MULTI-AGENT FRONTEND ROUTES

def proxy_multi_agent(method, path, payload=None):
    try:
        response = requests.request(
            method,
            f"{BACKEND_SERVICE_URL}{path}",
            json=payload,
            timeout=330,
        )
        return jsonify(response.json()), response.status_code

    except requests.Timeout:
        return jsonify({
            "error": "Multi-Agent request timed out."
        }), 504

    except (requests.RequestException, ValueError):
        return jsonify({
            "error": "Multi-Agent backend unavailable."
        }), 503


@app.post("/profiles/<int:profile_id>/multi-agent")
def start_profile_workflow(profile_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    return proxy_multi_agent(
        "POST",
        f"/api/profiles/{profile_id}/multi-agent",
        data,
    )


@app.get("/multi-agent/workflows/<uuid:workflow_id>")
def get_profile_workflow(workflow_id):
    return proxy_multi_agent(
        "GET",
        f"/api/multi-agent/workflows/{workflow_id}",
    )


@app.post("/multi-agent/workflows/<uuid:workflow_id>/human-review")
def review_profile_workflow(workflow_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    return proxy_multi_agent(
        "POST",
        f"/api/multi-agent/workflows/{workflow_id}/human-review",
        data,
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # noqa: S104 - required for container ingress
        port=5006,
        debug=os.getenv("FLASK_DEBUG", "false").lower()
        in ("true", "1", "yes"),
    )