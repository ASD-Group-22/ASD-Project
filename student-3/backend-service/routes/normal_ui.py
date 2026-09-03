from flask import Blueprint, request, jsonify
from services.database_api import SessionLocal
from models.project_requirement import ProjectRequirement
from models.group import Group

ui_bp = Blueprint('ui', __name__)

@ui_bp.post("/skills/create")
def create_skill_req():
    db = SessionLocal()
    data = request.json

    req = ProjectRequirement(
        subject=data['subject'],
        requirements=data['requirements'],
    )
    db.add(req)
    db.commit()

    return jsonify({"message": "Skill requirement created successfully."}), 201

@ui_bp.get("/groups/finalise")
def finalise_groups():
    db = SessionLocal()
    data = request.json

    group = Group(
        group_name=data['group_name'],
        members=data['members'],
    )
    db.add(group)
    db.commit()
    return jsonify({"message": "Group finalised successfully."}), 201

