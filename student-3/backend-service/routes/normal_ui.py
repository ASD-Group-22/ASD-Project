from flask import Blueprint, request, jsonify
from services.database_api import SessionLocal
from models.project_requirement import ProjectRequirement
from models.group import Group
from models.subject import Subject

ui_bp = Blueprint("ui", __name__)

# SUBJECTS
@ui_bp.get("/subjects")
def list_subjects():
    db = SessionLocal()
    subjects = db.query(Subject).all()
    db.close()
    return jsonify([s.name for s in subjects]), 200

# SKILL REQUIREMENTS
@ui_bp.post("/skills/create")
def create_skill_req():
    db = SessionLocal()
    data = request.get_json(force=True)

    subject = data["subject"]
    new_skill = data["requirements"]  # e.g. {"python": {"level": "...", "amount": "..."}}

    existing = db.query(ProjectRequirement).filter_by(subject=subject).first()

    if existing:
        # mutate JSON while session is open
        existing.requirements.update(new_skill)
        db.commit()

        # FORCE LOAD BEFORE CLOSING SESSION
        updated_requirements = dict(existing.requirements)

        db.close()
        return jsonify({
            "message": f"Added/updated skill(s) for subject '{subject}'.",
            "requirements": updated_requirements
        }), 200
    else:
        req = ProjectRequirement(subject=subject, requirements=new_skill)
        db.add(req)
        db.commit()

        # FORCE LOAD BEFORE CLOSING SESSION
        created_requirements = dict(req.requirements)

        db.close()
        return jsonify({
            "message": f"Created requirements for subject '{subject}'.",
            "requirements": created_requirements
        }), 201

@ui_bp.get("/skills/<subject>")
def read_requirements(subject):
    db = SessionLocal()
    req = db.query(ProjectRequirement).filter_by(subject=subject).first()

    if not req:
        db.close()
        return jsonify({"message": "No requirements found"}), 404

    # FORCE LOAD JSON BEFORE CLOSING SESSION
    requirements = dict(req.requirements)

    db.close()
    return jsonify(requirements), 200

@ui_bp.delete("/skills/delete/<subject>/<skill>")
def delete_requirement(subject, skill):
    db = SessionLocal()
    req = db.query(ProjectRequirement).filter_by(subject=subject).first()

    if not req or skill not in req.requirements:
        db.close()
        return jsonify({"message": "Skill not found"}), 404

    del req.requirements[skill]
    db.commit()

    # OPTIONAL: return updated requirements
    updated_requirements = dict(req.requirements)

    db.close()
    return jsonify({
        "message": f"Deleted skill '{skill}' from subject '{subject}'",
        "requirements": updated_requirements
    }), 200

# GROUPS
@ui_bp.post("/groups/finalise")
def finalise_groups():
    db = SessionLocal()
    data = request.get_json(force=True)

    group = Group(
        name=data["group_name"],
        members=data["members"]
    )
    db.add(group)
    db.commit()
    db.close()

    return jsonify({"message": "Group finalised successfully."}), 201

@ui_bp.get("/groups")
def list_groups():
    db = SessionLocal()
    groups = db.query(Group).all()
    db.close()
    return jsonify([
        {"group_name": g.name, "members": g.members}
        for g in groups
    ]), 200

@ui_bp.delete("/groups/delete/<group_name>")
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
