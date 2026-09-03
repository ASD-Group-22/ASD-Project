from flask import Blueprint, request, jsonify
from services.database_api import SessionLocal
from models.recommendation import Recommendation

rec_bp = Blueprint("recommendations", __name__)

@rec_bp.post("/create")
def create_recommendation():
    db = SessionLocal()
    data = request.get_json(force=True)

    subject = data["subject"]
    recommendation = data.get("recommendation", {})

    rec = Recommendation(subject=subject, recommendation=recommendation)
    db.add(rec)
    db.commit()
    db.close()

    return jsonify({
        "message": f"Recommendation created for {subject}",
        "recommendation": recommendation
    }), 201

@rec_bp.get("/read/<subject>")
def read_recommendation(subject):
    db = SessionLocal()
    rec = db.query(Recommendation).filter_by(subject=subject).first()
    db.close()

    if not rec:
        return jsonify({"message": "No recommendation found"}), 404

    return jsonify(rec.recommendation), 200
