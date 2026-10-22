import os
import requests
from flask import Blueprint, request, jsonify
from routes.ai_mode import group_recommendation
from group_recommendations import load_profiles, RecommendationError
from urllib.parse import quote

ui_bp = Blueprint("ui", __name__)

DB_URL = os.getenv("DB_URL", "http://database-service:6000")


@ui_bp.errorhandler(requests.RequestException)
def upstream_request_error(exc):
    if isinstance(exc, requests.Timeout):
        return jsonify(error='Database request timed out. Please try again.'), 504
    return jsonify(error='Database service is unavailable. Please try again.'), 502


# ---------------- SUBJECTS ----------------
@ui_bp.get("/subjects")
def list_subjects():
    res = requests.get(f"{DB_URL}/subjects", timeout=15)
    return jsonify(res.json()), res.status_code


# ---------------- SKILLS ----------------
@ui_bp.post("/skills/create")
def create_skill_req():
    data = request.get_json(force=True)
    subject = data["subject"]
    requirements = data["requirements"]

    res = requests.post(
        f"{DB_URL}/requirements",
        json={"subject": subject, "requirements": requirements},
        timeout=15,
    )

    return jsonify(res.json()), res.status_code


@ui_bp.get("/skills/<subject>")
def read_requirements(subject):
    res = requests.get(f"{DB_URL}/requirements/{subject}", timeout=15)
    return jsonify(res.json()), res.status_code


@ui_bp.delete("/skills/delete/<subject>/<path:skill>")
def delete_requirement(subject, skill):
    res = requests.delete(
        f"{DB_URL}/requirements/"
        f"{quote(subject, safe='')}/{quote(skill, safe='')}",
        timeout=15,
    )
    return jsonify(res.json()), res.status_code


# ---------------- GROUPS ----------------
@ui_bp.get("/groups")
def list_groups():
    res = requests.get(f"{DB_URL}/groups", timeout=15)
    return jsonify(res.json()), res.status_code


def validated_group():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RecommendationError('Send a group name and student IDs.', 400)
    name = data.get('group_name')
    members = data.get('members')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise RecommendationError('Group name must contain 1 to 100 characters.', 400)
    if not isinstance(members, list) or not members:
        raise RecommendationError('Choose at least one student ID.', 400)
    ids = []
    for member in members:
        if isinstance(member, str) and member.strip().isascii() and member.strip().isdigit():
            member = int(member.strip())
        if type(member) is not int or member <= 0:
            raise RecommendationError('Members must be positive student IDs, not names.', 400)
        ids.append(member)
    if len(ids) != len(set(ids)):
        raise RecommendationError('A student cannot appear twice in a group.', 400)
    known = {profile['student_id'] for profile in load_profiles()}
    invalid = sorted(set(ids) - known)
    if invalid:
        raise RecommendationError('Unknown student IDs: ' + ', '.join(map(str, invalid)), 400)
    return {'group_name': name.strip(), 'members': ids}


def write_group(group_id=None):
    try:
        payload = validated_group()
        if group_id is None:
            res = requests.post(f'{DB_URL}/groups', json=payload, timeout=15)
        else:
            res = requests.put(f'{DB_URL}/groups/by-id/{group_id}', json=payload, timeout=15)
        return jsonify(res.json()), res.status_code
    except RecommendationError as exc:
        return jsonify(error=str(exc)), exc.status
    except (requests.RequestException, ValueError):
        return jsonify(error='Group database unavailable. Reload groups before retrying.'), 502


@ui_bp.post('/groups/finalise')
def finalise_groups():
    return write_group()


@ui_bp.put('/groups/by-id/<int:group_id>')
def update_group_by_id(group_id):
    return write_group(group_id)


@ui_bp.delete('/groups/by-id/<int:group_id>')
def delete_group_by_id(group_id):
    try:
        res = requests.delete(f'{DB_URL}/groups/by-id/{group_id}', timeout=15)
        return jsonify(res.json()), res.status_code
    except (requests.RequestException, ValueError):
        return jsonify(error='Group database unavailable. Reload groups before retrying.'), 502


@ui_bp.delete("/groups/delete/<group_name>")
def delete_group(group_name):
    res = requests.delete(f"{DB_URL}/groups/{group_name}", timeout=15)
    return jsonify(res.json()), res.status_code


ui_bp.add_url_rule('/ai/group-recommendation', view_func=group_recommendation, methods=['POST'])
