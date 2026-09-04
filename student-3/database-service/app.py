from flask import Flask, request, jsonify
from services.database_api import SessionLocal
from models.project_requirement import ProjectRequirement
from models.group import Group
from models.subject import Subject
from models.recommendation import Recommendation
from models.student import Student
from services.database_api import Base, engine
Base.metadata.create_all(bind=engine)

app = Flask(__name__)


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

    if not req:
        db.close()
        return jsonify({}), 200

    requirements = dict(req.requirements)
    db.close()
    return jsonify(requirements), 200


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
        return jsonify({
            "message": f"Updated requirements for '{subject}'.",
            "requirements": updated
        }), 200

    req = ProjectRequirement(subject=subject, requirements=new_skill)
    db.add(req)
    db.commit()
    created = dict(req.requirements)
    db.close()
    return jsonify({
            "message": f"Created requirements for '{subject}'.",
            "requirements": created
    }), 201


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


# ---------------- STUDENTS ----------------
@app.get("/students")
def list_students():
    db = SessionLocal()
    students = db.query(Student).all()
    out = [{"name": s.name, "skills": s.skills} for s in students]
    db.close()
    return jsonify(out), 200


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

    group = Group(
        name=data["group_name"],
        members=data["members"]
    )

    db = SessionLocal()
    db.add(group)
    db.commit()
    db.close()
    return jsonify({"message": "Group created."}), 201


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
    return jsonify({"message": "Group deleted."}), 200


# ---------------- RECOMMENDATIONS ----------------
@app.post("/recommendations")
def create_recommendation():
    data = request.get_json(force=True)
    subject = data["subject"]
    recommendation = data.get("recommendation", {})

    db = SessionLocal()
    rec = Recommendation(subject=subject, recommendation=recommendation)
    db.add(rec)
    db.commit()
    db.close()

    return jsonify({
        "message": f"Recommendation created for {subject}",
        "recommendation": recommendation
    }), 201


@app.get("/recommendations/<subject>")
def read_recommendation(subject):
    db = SessionLocal()
    rec = db.query(Recommendation).filter_by(subject=subject).first()
    db.close()

    if not rec:
        return jsonify({"message": "No recommendation found"}), 404

    return jsonify(rec.recommendation), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
