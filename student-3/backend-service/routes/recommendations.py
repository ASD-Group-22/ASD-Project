import os
from urllib.parse import quote

import requests
from flask import Blueprint, jsonify, request

rec_bp = Blueprint('recommendations', __name__)
DB_URL = os.getenv('DB_URL', 'http://database-service:6000').rstrip('/')


def database_request(method, path, **kwargs):
    try:
        response = requests.request(method, f'{DB_URL}{path}', timeout=15, **kwargs)
        return jsonify(response.json()), response.status_code
    except (requests.RequestException, ValueError):
        return jsonify({'error': 'Recommendation database service is unavailable.'}), 503


@rec_bp.post('/create')
def create_recommendation():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Send a JSON object.'}), 400
    return database_request('POST', '/recommendations', json=data)


@rec_bp.get('/history')
def list_recommendations():
    return database_request('GET', '/recommendations',
                            params={'subject': request.args.get('subject', '').strip()})


@rec_bp.get('/history/<int:recommendation_id>')
def read_history_item(recommendation_id):
    return database_request('GET', f'/recommendations/history/{recommendation_id}')


@rec_bp.delete('/history/<int:recommendation_id>')
def delete_recommendation(recommendation_id):
    return database_request('DELETE', f'/recommendations/history/{recommendation_id}')


@rec_bp.get('/read/<subject>')
def read_recommendation(subject):
    return database_request('GET', f'/recommendations/{quote(subject, safe="")}')