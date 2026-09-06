from flask import Blueprint, request, jsonify
from group_recommendations import RecommendationError, load_profiles, recommend

ai_bp = Blueprint('ai', __name__)


@ai_bp.get('/profiles')
def profiles():
    try:
        return jsonify(load_profiles()), 200
    except RecommendationError as exc:
        return jsonify({'error': str(exc)}), exc.status


@ai_bp.post('/group-recommendation')
def group_recommendation():
    try:
        return jsonify(recommend(request.get_json(silent=True))), 200
    except RecommendationError as exc:
        return jsonify({'error': str(exc)}), exc.status
