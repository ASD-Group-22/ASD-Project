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

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5006,
        debug=True
    )
