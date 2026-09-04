import os
import requests
from flask import Blueprint, request, jsonify
from llm_client import ask_llm

ui_bp = Blueprint("ui", __name__)

DB_URL = os.getenv("DB_URL", "http://database-service:6000")


# ---------------- SUBJECTS ----------------
@ui_bp.get("/subjects")
def list_subjects():
    res = requests.get(f"{DB_URL}/subjects")
    return jsonify(res.json()), res.status_code


# ---------------- SKILLS ----------------
@ui_bp.post("/skills/create")
def create_skill_req():
    data = request.get_json(force=True)
    subject = data["subject"]
    requirements = data["requirements"]

    res = requests.post(
        f"{DB_URL}/requirements",
        json={"subject": subject, "requirements": requirements}
    )

    return jsonify(res.json()), res.status_code


@ui_bp.get("/skills/<subject>")
def read_requirements(subject):
    res = requests.get(f"{DB_URL}/requirements/{subject}")
    return jsonify(res.json()), res.status_code


@ui_bp.delete("/skills/delete/<subject>/<skill>")
def delete_requirement(subject, skill):
    # DB-service returns updated requirements JSON
    res = requests.delete(f"{DB_URL}/requirements/{subject}/{skill}")
    return jsonify(res.json()), res.status_code


# ---------------- GROUPS ----------------
@ui_bp.get("/groups")
def list_groups():
    res = requests.get(f"{DB_URL}/groups")
    return jsonify(res.json()), res.status_code


@ui_bp.post("/groups/finalise")
def finalise_groups():
    data = request.get_json(force=True)
    res = requests.post(f"{DB_URL}/groups", json=data)
    return jsonify(res.json()), res.status_code


@ui_bp.delete("/groups/delete/<group_name>")
def delete_group(group_name):
    res = requests.delete(f"{DB_URL}/groups/{group_name}")
    return jsonify(res.json()), res.status_code


# ---------------- AI RECOMMENDATION (simple) ----------------
@ui_bp.post("/ai/group-recommendation")
def ai_group_recommendation():
    data = request.get_json(force=True)
    subject = data["subject"]

    req_res = requests.get(f"{DB_URL}/requirements/{subject}")
    requirements = req_res.json()

    prompt = f"""
You are an AI assistant helping form groups for subject '{subject}'.

Project requirements:
{requirements}

Return a JSON structure describing recommended groups.
"""

    answer = ask_llm(prompt)
    return jsonify({"recommendation": answer}), 200
