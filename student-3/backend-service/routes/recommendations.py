import os
import requests
from flask import Blueprint, request, jsonify

rec_bp = Blueprint("recommendations", __name__)
DB_URL = os.getenv("DB_URL", "http://database-service:6000")


@rec_bp.post("/create")
def create_recommendation():
    data = request.get_json(force=True)

    res = requests.post(f"{DB_URL}/recommendations", json=data)
    return jsonify(res.json()), res.status_code


@rec_bp.get("/read/<subject>")
def read_recommendation(subject):
    res = requests.get(f"{DB_URL}/recommendations/{subject}")
    return jsonify(res.json()), res.status_code
