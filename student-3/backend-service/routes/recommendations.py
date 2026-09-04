import os
import requests
<<<<<<< HEAD
from flask import Blueprint, jsonify, request
=======
from flask import Blueprint, request, jsonify
>>>>>>> e9c0fc0c277d73d0205f7956d635768df3270521

rec_bp = Blueprint("recommendations", __name__)
DB_URL = os.getenv("DB_URL", "http://database-service:6000")

<<<<<<< HEAD
@rec_bp.post("/create")
def create_recommendation():
    data = request.get_json(force=True)
    res = requests.post(f"{DB_URL}/recommendations", json=data)
    return jsonify(res.json()), res.status_code

=======

@rec_bp.post("/create")
def create_recommendation():
    data = request.get_json(force=True)

    res = requests.post(f"{DB_URL}/recommendations", json=data)
    return jsonify(res.json()), res.status_code


>>>>>>> e9c0fc0c277d73d0205f7956d635768df3270521
@rec_bp.get("/read/<subject>")
def read_recommendation(subject):
    res = requests.get(f"{DB_URL}/recommendations/{subject}")
    return jsonify(res.json()), res.status_code
