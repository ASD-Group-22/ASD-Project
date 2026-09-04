from flask import Flask, request, jsonify
from services.database_api import Base, engine, SessionLocal
from models.project_requirement import ProjectRequirement
from models.group import Group
from models.subject import Subject
from models.recommendation import Recommendation
from models.student import Student

app = Flask(__name__)

Base.metadata.create_all(bind=engine)

# ---------------- SUBJECTS ----------------
@app.get("/subjects")
def list_subjects():
    db = SessionLocal()
    subjects = db.query(Subject).all()
    names = [s.name for s in subjects]
    db.close()
    return jsonify(names), 200

# ---------------- REQUIREMENTS ----------------
@app.get("/requirements/<subject>")
def get_requirements(subject):
    db = SessionLocal()
    req = db.query(ProjectRequirement).filter_by(subject=subject).first()
    db.close()
    return jsonify(req.requirements if req else {}), 200

@app.post("/requirements")
def create_or_update_requirements():
    data = request.get_json(force=True)
    subject = data["subject"]
    new_skill = data["requirements"]

    db = SessionLocal()
    existing = db.query(ProjectRequirement).filter_by(subject=subject).first()

    if existing:
        existing.requirements.update(new_skill)
        db.commit()
        updated = dict(existing.requirements)
        db.close()
        return jsonify({"message": "Updated", "requirements": updated}), 200

    req = ProjectRequirement(subject=subject, requirements=new_skill)
    db.add(req)
    db.commit()
    created = dict(req.requirements)
    db.close()
    return jsonify({"message": "Created", "requirements": created}), 201

@app.delete("/requirements/<subject>/<skill>")
def delete_skill(subject, skill):
    db = SessionLocal()
    req = db.query(ProjectRequirement).filter_by(subject=subject).first()

    if not req or skill not in req.requirements:
        db.close()
        return jsonify({"message": "Skill not found"}), 404

    del req.requirements[skill]
    db.commit()
    updated = dict(req.requirements)
    db.close()
    return jsonify(updated), 200

# ---------------- STUDENTS (PLACEHOLDER) ----------------
@app.get("/students")
def list_students():
    placeholder_students = [
        {
            "name": "Alice Nguyen",
            "skills": {"python": 4, "java": 2, "documentation": 5, "research": 3, "diagramming": 4}
        },
        {
            "name": "Ben Carter",
            "skills": {"python": 1, "java": 5, "documentation": 2, "research": 4, "diagramming": 3}
        },
        {
            "name": "Chloe Singh",
            "skills": {"python": 3, "java": 3, "documentation": 4, "research": 5, "diagramming": 2}
        },
        {
            "name": "Daniel Kim",
            "skills": {"python": 5, "java": 1, "documentation": 3, "research": 2, "diagramming": 5}
        },
        {
            "name": "Emily Zhao",
            "skills": {"python": 2, "java": 4, "documentation": 5, "research": 3, "diagramming": 4}
        }
    ]
    return jsonify(placeholder_students), 200

# ---------------- GROUPS ----------------
@app.get("/groups")
def list_groups():
    db = SessionLocal()
    groups = db.query(Group).all()
    out = [{"group_name": g.name, "members": g.members} for g in groups]
    db.close()
    return jsonify(out), 200

@app.post("/groups")
def create_group():
    data = request.get_json(force=True)
    group = Group(name=data["group_name"], members=data["members"])
    db = SessionLocal()
    db.add(group)
    db.commit()
    db.close()
    return jsonify({"message": "Group created"}), 201

@app.delete("/groups/<group_name>")
def delete_group(group_name):
    db = SessionLocal()
    group = db.query(Group).filter_by(name=group_name).first()
    if not group:
        db.close()
        return jsonify({"message": "Group not found"}), 404
    db.delete(group)
    db.commit()
    db.close()
    return jsonify({"message": "Group deleted"}), 200

# ---------------- RECOMMENDATIONS ----------------
@app.post("/recommendations")
def create_recommendation():
    data = request.get_json(force=True)
    subject = data["subject"]
    recommendation = data["recommendation"]

    db = SessionLocal()
    rec = Recommendation(subject=subject, recommendation=recommendation)
    db.add(rec)
    db.commit()
    db.close()

    return jsonify({"message": "Recommendation saved"}), 201

@app.get("/recommendations/<subject>")
def read_recommendation(subject):
    db = SessionLocal()
    rec = db.query(Recommendation).filter_by(subject=subject).first()
    db.close()
    return jsonify(rec.recommendation if rec else {}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
