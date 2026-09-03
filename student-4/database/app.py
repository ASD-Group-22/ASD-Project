from flask import Flask, request, jsonify
import sqlite3
import os


app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "skill_profile.db")


def get_db_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# DATABASE HEALTH CHECK
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "service": "Skill Profile Database Service",
        "status": "running"
    })


# CREATE PROFILE
@app.route("/profiles", methods=["POST"])
def create_profile():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    student_id = data.get("student_id")
    skills = data.get("skills", [])

    if not student_id:
        return jsonify({
            "error": "student_id is required"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO skill_profiles (student_id)
        VALUES (?)
    """, (student_id,))

    profile_id = cursor.lastrowid

    for skill in skills:

        cursor.execute("""
            INSERT INTO student_skills (
                profile_id,
                skill_name,
                skill_level,
                strength,
                weakness
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            profile_id,
            skill.get("skill_name"),
            skill.get("skill_level"),
            skill.get("strength"),
            skill.get("weakness")
        ))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Skill profile created successfully",
        "profile_id": profile_id
    }), 201


# GET PROFILE
@app.route("/profiles/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):

    connection = get_db_connection()

    profile = connection.execute("""
        SELECT *
        FROM skill_profiles
        WHERE profile_id = ?
    """, (profile_id,)).fetchone()

    if profile is None:

        connection.close()

        return jsonify({
            "error": "Profile not found"
        }), 404

    skills = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE profile_id = ?
    """, (profile_id,)).fetchall()

    connection.close()

    profile_data = dict(profile)

    profile_data["skills"] = [
        dict(skill)
        for skill in skills
    ]

    return jsonify(profile_data), 200

# UPDATE PROFILE
@app.route("/profiles/<int:profile_id>", methods=["PUT"])
def update_profile(profile_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data provided"
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    profile = cursor.execute("""
        SELECT *
        FROM skill_profiles
        WHERE profile_id = ?
    """, (profile_id,)).fetchone()

    if profile is None:
        connection.close()

        return jsonify({
            "error": "Profile not found"
        }), 404

    student_id = data.get("student_id")

    if student_id:
        cursor.execute("""
            UPDATE skill_profiles
            SET student_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE profile_id = ?
        """, (
            student_id,
            profile_id
        ))

    # Replace skills if new skill data is supplied
    if "skills" in data:

        cursor.execute("""
            DELETE FROM student_skills
            WHERE profile_id = ?
        """, (profile_id,))

        skills = data.get("skills", [])

        for skill in skills:

            cursor.execute("""
                INSERT INTO student_skills (
                    profile_id,
                    skill_name,
                    skill_level,
                    strength,
                    weakness
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                profile_id,
                skill.get("skill_name"),
                skill.get("skill_level"),
                skill.get("strength"),
                skill.get("weakness")
            ))

    cursor.execute("""
        UPDATE skill_profiles
        SET updated_at = CURRENT_TIMESTAMP
        WHERE profile_id = ?
    """, (profile_id,))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Skill profile updated successfully",
        "profile_id": profile_id
    }), 200

# DELETE PROFILE
@app.route("/profiles/<int:profile_id>", methods=["DELETE"])
def delete_profile(profile_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    profile = cursor.execute("""
        SELECT *
        FROM skill_profiles
        WHERE profile_id = ?
    """, (profile_id,)).fetchone()

    if profile is None:
        connection.close()

        return jsonify({
            "error": "Profile not found"
        }), 404

    cursor.execute("""
        DELETE FROM student_skills
        WHERE profile_id = ?
    """, (profile_id,))

    cursor.execute("""
        DELETE FROM skill_profiles
        WHERE profile_id = ?
    """, (profile_id,))

    connection.commit()
    connection.close()

    return jsonify({
        "message": "Skill profile deleted successfully",
        "profile_id": profile_id
    }), 200

# GET PROFILE BY STUDENT ID
@app.route("/profiles/student/<int:student_id>", methods=["GET"])
def get_profile_by_student_id(student_id):

    connection = get_db_connection()

    profile = connection.execute("""
        SELECT *
        FROM skill_profiles
        WHERE student_id = ?
        ORDER BY profile_id DESC
        LIMIT 1
    """, (student_id,)).fetchone()

    if profile is None:

        connection.close()

        return jsonify({
            "error": "Profile not found"
        }), 404

    skills = connection.execute("""
        SELECT *
        FROM student_skills
        WHERE profile_id = ?
    """, (profile["profile_id"],)).fetchall()

    connection.close()

    profile_data = dict(profile)

    profile_data["skills"] = [
        dict(skill)
        for skill in skills
    ]

    return jsonify(profile_data), 200

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5004,
        debug=True
    )