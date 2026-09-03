from flask import Blueprint, jsonify, request
import requests

from services.database_api import (
    create_listing_response,
    deactivate_listing_response,
    get_listing_response,
    get_listings,
    search_listings,
    update_listing_response,
)
from services.matching_service import deterministic_candidates

normal_ui_bp = Blueprint("normal_ui", __name__)


def _payload_error(payload):
    required = ["student_id", "student_name", "skill_offered", "skill_wanted", "availability"]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        return "Missing required fields: " + ", ".join(missing)
    try:
        if int(payload["student_id"]) <= 0:
            return "student_id must be a positive integer"
        
    except (TypeError, ValueError):
        return "student_id must be a positive integer"
    
    if payload.get("status", "active") not in {"active", "inactive"}:
        return "status must be active or inactive"
    
    return None


@normal_ui_bp.get("/")
def health():
    return jsonify({"service": "student-2-skill-exchange-backend", "status": "running"}), 200


@normal_ui_bp.get("/skill-exchange")
def get_all_listings():
    try:
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"
        return jsonify({"listings": get_listings(include_inactive=include_inactive)}), 200
    
    except requests.RequestException as exc:
        return jsonify({"error": f"database-service unavailable: {exc}"}), 503


@normal_ui_bp.get("/skill-exchange/search")
def search():
    skill = request.args.get("skill", "").strip()

    if not skill:
        return jsonify({"error": "skill query is required"}), 400
    
    try:
        return jsonify({"listings": search_listings(skill)}), 200
    
    except requests.RequestException as exc:
        return jsonify({"error": f"database-service unavailable: {exc}"}), 503


@normal_ui_bp.get("/skill-exchange/<int:listing_id>")
def get_one_listing(listing_id):
    try:
        response = get_listing_response(listing_id)
        return jsonify(response.json()), response.status_code
    
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"database-service request failed: {exc}"}), 503


@normal_ui_bp.post("/skill-exchange")
def create_listing():
    payload = request.get_json(silent=True) or {}
    error = _payload_error(payload)

    if error:
        return jsonify({"error": error}), 400
    try:
        response = create_listing_response(payload)
        return jsonify(response.json()), response.status_code
    
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"database-service request failed: {exc}"}), 503


@normal_ui_bp.put("/skill-exchange/<int:listing_id>")
def update_listing(listing_id):
    payload = request.get_json(silent=True) or {}
    error = _payload_error(payload)

    if error:
        return jsonify({"error": error}), 400
    
    try:
        response = update_listing_response(listing_id, payload)
        return jsonify(response.json()), response.status_code
    
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"database-service request failed: {exc}"}), 503


@normal_ui_bp.delete("/skill-exchange/<int:listing_id>")
def delete_listing(listing_id):
    try:
        response = deactivate_listing_response(listing_id)
        return jsonify(response.json()), response.status_code
    
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"database-service request failed: {exc}"}), 503


@normal_ui_bp.get("/skill-exchange/<int:listing_id>/matches")
def get_candidate_matches(listing_id):
    try:
        target_response = get_listing_response(listing_id)

        if target_response.status_code == 404:
            return jsonify({"error": "Listing not found"}), 404
        
        target_response.raise_for_status()
        target = target_response.json()
        if target.get("status") != "active":
            return jsonify({
                "error": "Inactive listings cannot request matches"
            }), 409   
        
        candidates = deterministic_candidates(target, get_listings(include_inactive=False))

        return jsonify({"listing": target, "candidates": candidates}), 200
    
    except (requests.RequestException, ValueError) as exc:
        return jsonify({"error": f"candidate retrieval failed: {exc}"}), 503
