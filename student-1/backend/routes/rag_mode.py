from flask import (
    Blueprint,
    jsonify,
    request,
)

from services.rag_api import (
    answer_question,
    rag_is_enabled,
    refresh_corpus,
    retrieve_context,
)


rag_bp = Blueprint(
    "rag_mode",
    __name__,
)


def disabled_response():

    return jsonify({
        "status": "disabled",
        "error": "RAG Mode is disabled",
    }), 503


@rag_bp.get("/rag/status")
def rag_status():

    return jsonify({
        "status": (
            "enabled"
            if rag_is_enabled()
            else "disabled"
        ),
        "rag_enabled": rag_is_enabled(),
    })


@rag_bp.post("/rag/refresh")
def rag_refresh():

    if not rag_is_enabled():
        return disabled_response()

    try:

        result = refresh_corpus()

        return jsonify(result)

    except Exception as exc:

        return jsonify({
            "status": "error",
            "error": (
                f"RAG request failed: {exc}"
            ),
        }), 503


@rag_bp.post("/rag/retrieve")
def rag_retrieve():

    if not rag_is_enabled():
        return disabled_response()

    data = request.get_json(
        silent=True
    ) or {}

    query = str(
        data.get(
            "query",
            ""
        )
    ).strip()

    if not query:

        return jsonify({
            "status": "error",
            "error": "query is required",
        }), 400

    try:

        k = int(
            data.get(
                "k",
                5
            )
        )

        if k <= 0:
            raise ValueError

    except (
        TypeError,
        ValueError,
    ):

        return jsonify({
            "status": "error",
            "error": (
                "k must be a positive integer"
            ),
        }), 400

    try:

        result = retrieve_context(
            query=query,
            k=k,
        )

        return jsonify(result)

    except Exception as exc:

        return jsonify({
            "status": "error",
            "error": (
                f"RAG request failed: {exc}"
            ),
        }), 503


@rag_bp.post("/rag/answer")
def rag_answer():

    if not rag_is_enabled():
        return disabled_response()

    data = request.get_json(
        silent=True
    ) or {}

    query = str(
        data.get(
            "query",
            ""
        )
    ).strip()

    if not query:

        return jsonify({
            "status": "error",
            "error": "query is required",
        }), 400

    try:

        k = int(
            data.get(
                "k",
                5
            )
        )

        if k <= 0:
            raise ValueError

    except (
        TypeError,
        ValueError,
    ):

        return jsonify({
            "status": "error",
            "error": (
                "k must be a positive integer"
            ),
        }), 400

    try:

        result = answer_question(
            query=query,
            k=k,
        )

        return jsonify(result)

    except Exception as exc:

        return jsonify({
            "status": "error",
            "error": (
                f"RAG request failed: {exc}"
            ),
        }), 503
