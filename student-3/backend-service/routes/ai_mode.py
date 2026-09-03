from flask import Blueprint, request, jsonify
from services.database_api import SessionLocal
from models.project_requirement import ProjectRequirement
from models.student import Student
from services.llm_client import run_llm
from services.prompt_loader import load_prompt

ai_bp = Blueprint('ai_mode', __name__)

@ai_bp.post("/group-recommendation")
def group_recommendation():
    db = SessionLocal()
    data = request.json

    subject = data['subject']
    model = data.get("model", "deepseek-r1:8b")

    req = db.query(ProjectRequirement).filter_by(subject=subject).first()
    students = db.query(Student).all()

    if not req or not students:
        return jsonify({"error": "Missing requirements/students."}), 400

    prompt_template = load_prompt("group_balance_prompt")

    student_data = [
        dict(id=s.id, name=s.name, email=s.email, skills=s.skills) 
        for s in students
    ]

    prompt = (
        prompt_template
        .replace("{{students}}", str(student_data))
        .replace("{{requirements}}", str(req.requirements))
    )

    result = run_llm(model=model, prompt=prompt)

    return jsonify({"recommendation": result}), 200