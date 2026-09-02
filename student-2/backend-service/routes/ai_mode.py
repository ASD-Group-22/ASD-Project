from flask import Blueprint, jsonify
import requests

from services.database_api import get_listing_response
from services.matching_service import run_agentic_match

ai_mode_bp = Blueprint("ai_mode", __name__)


@ai_mode_bp.post("/skill-exchange/<int:listing_id>/ai-match")
def ai_match(listing_id):
    try:
        target_response = get_listing_response(listing_id)
        if target_response.status_code == 404:
            return jsonify({"error": "Listing not found"}), 404
        
        target_response.raise_for_status()
        target = target_response.json()
        if target.get("status") != "active":
            return jsonify({
                "error": "Inactive listings cannot request AI recommendations"
            }), 409
        
        result = run_agentic_match(target)
        return jsonify({"listing": target, **result}), 200
    
    except requests.RequestException as exc:
        return jsonify({"error": f"application evidence retrieval failed: {exc}"}), 503
    
    except Exception as exc:
        return jsonify({"error": f"AI-assisted match failed: {exc}"}), 503
