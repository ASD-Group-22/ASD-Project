from flask import Blueprint, request, jsonify
from services.database_api import SessionLocal
from models.project_requirement import ProjectRequirement
from models.student import Student

ai_bp = Blueprint("ai", __name__)

@ai_bp.post("/group-recommendation")
def group_recommendation():
    db = SessionLocal()
    data = request.get_json(force=True)

    subject = data["subject"]

    req = db.query(ProjectRequirement).filter_by(subject=subject).first()
    requirements = req.requirements if req else {}

    students = db.query(Student).all()
    student_profiles = [
        {"name": s.name, "skills": s.skills}
        for s in students
    ]

    # Dummy logic: first 4 students
    recommended = [s.name for s in students[:4]]

    db.close()

    return jsonify({
        "subject": subject,
        "requirements": requirements,
        "students": student_profiles,
        "recommended_group": recommended,
        "reasoning": "Dummy logic using real student profiles."
    }), 200
