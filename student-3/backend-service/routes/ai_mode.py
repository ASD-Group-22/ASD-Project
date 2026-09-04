import os
import requests
from flask import Blueprint, request, jsonify
from llm_client import ask_llm

ai_bp = Blueprint("ai", __name__)
DB_URL = os.getenv("DB_URL", "http://database-service:6000")


@ai_bp.post("/group-recommendation")
def group_recommendation():
    data = request.get_json(force=True)
    subject = data["subject"]

    # requirements
    req_res = requests.get(f"{DB_URL}/requirements/{subject}")
    requirements = req_res.json()

    # students
    students_res = requests.get(f"{DB_URL}/students")
    students = students_res.json()

    prompt = f"""
You are an AI assistant helping form groups for subject '{subject}'.

Project requirements:
{requirements}

Student profiles:
{students}

Return a JSON structure describing recommended groups.
"""

    answer = ask_llm(prompt)

    return jsonify({
        "subject": subject,
        "requirements": requirements,
        "students": students,
        "recommendation": answer
    }), 200
