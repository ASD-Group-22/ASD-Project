import os
from flask import Blueprint, request, jsonify
from group_recommendations import RecommendationError, load_profiles, recommend

ai_bp = Blueprint('ai', __name__)


@ai_bp.get('/profiles')
def profiles():
    try:
        return jsonify(load_profiles()), 200
    except RecommendationError as exc:
        return jsonify({'error': str(exc), 'loop': getattr(exc, 'loop', None)}), exc.status


@ai_bp.post('/group-recommendation')
def group_recommendation():
    if os.getenv('AI_ENABLED', 'true').strip().lower() not in ('1', 'true', 'yes', 'on'):
        return jsonify({'error': 'AI mode is disabled.'}), 503
    try:
        return jsonify(recommend(request.get_json(silent=True))), 200
    except RecommendationError as exc:
        return jsonify({'error': str(exc), 'loop': getattr(exc, 'loop', None)}), exc.status
