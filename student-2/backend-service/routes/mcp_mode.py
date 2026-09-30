from flask import Blueprint, jsonify, request

from services.mcp_api import (
    get_listing,
    mcp_is_enabled,
    search_skills,
)


mcp_mode_bp = Blueprint(
    "mcp_mode",
    __name__,
)


def _disabled_response():
    return jsonify({
        "status": "disabled",
        "error": "MCP Mode is disabled",
    }), 403


@mcp_mode_bp.get("/mcp/status")
def mcp_status():
    return jsonify({
        "status": "enabled" if mcp_is_enabled() else "disabled",
        "mcp_enabled": mcp_is_enabled(),
    }), 200


@mcp_mode_bp.post("/mcp/search-skills")
def mcp_search_skills():
    if not mcp_is_enabled():
        return _disabled_response()

    payload = request.get_json(
        silent=True,
    ) or request.form

    skill = str(
        payload.get("skill", "")
    ).strip()

    if not skill:
        return jsonify({
            "status": "error",
            "error": "skill is required",
        }), 400

    try:
        result = search_skills(skill)

        status_code = (
            200
            if result.get("status") == "success"
            else 502
        )

        return jsonify(result), status_code

    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": f"MCP request failed: {exc}",
        }), 503


@mcp_mode_bp.post(
    "/mcp/listing/<int:listing_id>"
)
def mcp_get_listing(listing_id):
    if not mcp_is_enabled():
        return _disabled_response()

    try:
        result = get_listing(listing_id)

        if (
            result.get("status") == "error"
            and result.get("error") == "Listing not found"
        ):
            return jsonify(result), 404

        status_code = (
            200
            if result.get("status") == "success"
            else 502
        )

        return jsonify(result), status_code

    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": f"MCP request failed: {exc}",
        }), 503
