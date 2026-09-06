from flask import Flask, request, jsonify
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
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

@app.delete("/requirements/<subject>/<path:skill>")
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

# ---------------- RECOMMENDATION HISTORY ----------------
# Store history metadata inside the existing JSON column, so existing SQLite
# databases need no schema migration. Older records remain readable.
def history_record(rec, include_snapshot=True):
    payload = rec.recommendation

    if (isinstance(payload, dict) and payload.get('history_version') == 1
            and isinstance(payload.get('snapshot'), dict)):
        snapshot = payload['snapshot']
        saved_at = payload.get('saved_at')
    else:
        snapshot = {'subject': rec.subject, 'recommendation': payload}
        saved_at = None

    recommendation = snapshot.get('recommendation')
    groups = recommendation.get('groups') if isinstance(recommendation, dict) else None
    result = {
        'id': rec.id,
        'subject': rec.subject,
        'saved_at': saved_at,
        'model': snapshot.get('model'),
        'group_count': len(groups) if isinstance(groups, list) else None,
    }

    if include_snapshot:
        result['snapshot'] = snapshot

    return result


@app.post('/recommendations')
def create_recommendation():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({'error': 'Send a JSON object.'}), 400

    subject = data.get('subject')
    recommendation = data.get('recommendation')

    if not isinstance(subject, str) or not subject.strip():
        return jsonify({'error': 'A subject is required.'}), 400

    if not isinstance(recommendation, (dict, str)) or not recommendation:
        return jsonify({'error': 'A nonempty recommendation object or text is required.'}), 400

    if isinstance(recommendation, str) and not recommendation.strip():
        return jsonify({'error': 'Recommendation text cannot be blank.'}), 400

    snapshot = {key: data[key] for key in (
        'recommendation', 'requirements', 'students', 'model', 'profile_source', 'attempts', 'note'
    ) if key in data}

    snapshot['subject'] = subject.strip()
    payload = {
        'history_version': 1,
        'saved_at': datetime.now(timezone.utc).isoformat(),
        'snapshot': snapshot,
    }

    db = SessionLocal()

    try:
        rec = Recommendation(subject=subject.strip(), recommendation=payload)
        db.add(rec)
        db.commit()
        result = history_record(rec)
        return jsonify({'message': 'Recommendation saved.', **result}), 201
    except SQLAlchemyError:
        db.rollback()
        app.logger.exception('Could not save recommendation')
        return jsonify({'error': 'Could not save recommendation.'}), 500
    finally:
        db.close()


@app.get('/recommendations')
def list_recommendations():
    subject = request.args.get('subject', '').strip()
    db = SessionLocal()
    try:
        query = db.query(Recommendation)
        if subject:
            query = query.filter_by(subject=subject)
        records = query.order_by(Recommendation.id.desc()).all()
        return jsonify([history_record(rec, False) for rec in records]), 200
    finally:
        db.close()


@app.get('/recommendations/history/<int:recommendation_id>')
def read_history_item(recommendation_id):
    db = SessionLocal()
    try:
        rec = db.get(Recommendation, recommendation_id)

        if rec is None:
            return jsonify({'error': 'Recommendation not found.'}), 404

        return jsonify(history_record(rec)), 200
    finally:
        db.close()


@app.delete('/recommendations/history/<int:recommendation_id>')
def delete_recommendation(recommendation_id):
    db = SessionLocal()
    try:
        rec = db.get(Recommendation, recommendation_id)

        if rec is None:
            return jsonify({'error': 'Recommendation not found.'}), 404

        db.delete(rec)
        db.commit()

        return jsonify({'message': 'Recommendation deleted.', 'id': recommendation_id}), 200
    except SQLAlchemyError:
        db.rollback()
        app.logger.exception('Could not delete recommendation')
        return jsonify({'error': 'Could not delete recommendation.'}), 500
    finally:
        db.close()


# Preserve the old read-by-subject endpoint, returning the newest saved result.
@app.get('/recommendations/<subject>')
def read_recommendation(subject):
    db = SessionLocal()
    try:
        rec = db.query(Recommendation).filter_by(subject=subject).order_by(Recommendation.id.desc()).first()
        return jsonify(history_record(rec)['snapshot']['recommendation'] if rec else {}), 200
    finally:
        db.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)