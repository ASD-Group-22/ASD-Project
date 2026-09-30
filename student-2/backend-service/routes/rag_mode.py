from flask import Blueprint, jsonify, request
import requests

from services.rag_api import (
    answer_question,
    rag_is_enabled,
    refresh_corpus,
    retrieve_context,
)


rag_mode_bp = Blueprint(
    "rag_mode",
    __name__,
)


def request_payload() -> dict:
    payload = request.get_json(
        silent=True,
    )

    if isinstance(
        payload,
        dict,
    ):
        return payload

    return request.form.to_dict()


def parse_k(
    value,
) -> int:
    if value in (
        None,
        "",
    ):
        return 5

    try:
        parsed = int(value)
    except (
        TypeError,
        ValueError,
    ):
        raise ValueError(
            "k must be an integer"
        )

    return max(
        1,
        min(
            parsed,
            10,
        ),
    )


def disabled_response():
    return jsonify({
        "status": "disabled",
        "error": (
            "RAG Mode is disabled"
        ),
    }), 403


@rag_mode_bp.get("/rag/status")
def rag_status():
    enabled = rag_is_enabled()

    return jsonify({
        "rag_enabled": enabled,
        "status": (
            "enabled"
            if enabled
            else "disabled"
        ),
    }), 200


@rag_mode_bp.post("/rag/refresh")
def rag_refresh():
    if not rag_is_enabled():
        return disabled_response()

    try:
        result = refresh_corpus()

        return jsonify(
            result
        ), 200

    except (
        requests.RequestException,
        RuntimeError,
    ) as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 503


@rag_mode_bp.post("/rag/retrieve")
def rag_retrieve():
    if not rag_is_enabled():
        return disabled_response()

    payload = request_payload()

    query = str(
        payload.get(
            "query",
            "",
        )
    ).strip()

    if not query:
        return jsonify({
            "status": "error",
            "error": (
                "query is required"
            ),
        }), 400

    try:
        k = parse_k(
            payload.get("k")
        )

        result = retrieve_context(
            query,
            k,
        )

        return jsonify(
            result
        ), 200

    except ValueError as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 400

    except (
        requests.RequestException,
        RuntimeError,
    ) as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 503


@rag_mode_bp.post("/rag/answer")
def rag_answer():
    if not rag_is_enabled():
        return disabled_response()

    payload = request_payload()

    query = str(
        payload.get(
            "query",
            "",
        )
    ).strip()

    if not query:
        return jsonify({
            "status": "error",
            "error": (
                "query is required"
            ),
        }), 400

    try:
        k = parse_k(
            payload.get("k")
        )

        result = answer_question(
            query,
            k,
        )

        return jsonify(
            result
        ), 200

    except ValueError as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 400

    except (
        requests.RequestException,
        RuntimeError,
    ) as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 503