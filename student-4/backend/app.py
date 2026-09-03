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

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5005,
        debug=True
    )
