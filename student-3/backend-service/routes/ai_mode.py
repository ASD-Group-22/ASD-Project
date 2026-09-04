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

    # Requirements
    req_res = requests.get(f"{DB_URL}/requirements/{subject}")
    requirements = req_res.json()

    # Students
    students_res = requests.get(f"{DB_URL}/students")
    students = students_res.json()

    prompt = f"""
You are an expert in team formation for university software engineering projects.

Your job is to create a balanced project group for the subject '{subject}'.

### Project Requirements
{requirements}

### Student Skill Profiles
{students}

### Your Task
- Form a single recommended group of 3–5 students.
- Ensure the group collectively satisfies ALL project skill requirements.
- Balance the group so strengths and weaknesses complement each other.
- Prefer diversity of skill sets over stacking identical skills.
- Explain your reasoning clearly.

### Output Format (JSON)
Return ONLY valid JSON in this format:

{
  "recommended_group": ["Student A", "Student B", ...],
  "reasoning": "Explain why these students form a balanced group."
}
"""

    answer = ask_llm(prompt)

    return jsonify({
        "subject": subject,
        "requirements": requirements,
        "students": students,
        "recommendation": answer
    }), 200
