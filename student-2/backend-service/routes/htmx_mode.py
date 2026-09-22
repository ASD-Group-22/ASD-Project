"""HTML-fragment endpoints used by the Student 2 HTMX frontend.

The existing JSON MCP and RAG routes remain available for API testing,
CI validation and integration evidence.

These routes provide a thin presentation layer only.
"""

from flask import Blueprint, request

from services.mcp_api import (
    get_listing,
    mcp_is_enabled,
    search_skills,
)
from services.rag_api import (
    answer_question,
    rag_is_enabled,
    refresh_corpus,
    retrieve_context,
)
from views.html_formatters import (
    format_error,
    format_mcp_result,
    format_rag_answer,
    format_rag_refresh,
    format_rag_retrieval,
    format_service_status,
)


htmx_mode_bp = Blueprint(
    "htmx_mode",
    __name__,
)


def _parse_k(value) -> int:
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


@htmx_mode_bp.get("/htmx/mcp/status")
def htmx_mcp_status():
    enabled = mcp_is_enabled()

    message = (
        "MCP Mode is enabled and configured for Student 2."
        if enabled
        else "MCP Mode is disabled."
    )

    return format_service_status(
        message,
        enabled,
    ), 200


@htmx_mode_bp.post("/htmx/mcp/search-skills")
def htmx_mcp_search_skills():
    if not mcp_is_enabled():
        return format_error(
            "MCP Mode is disabled."
        ), 200

    skill = str(
        request.form.get(
            "skill",
            "",
        )
    ).strip()

    if not skill:
        return format_error(
            "A skill is required."
        ), 200

    try:
        result = search_skills(
            skill,
        )

        return format_mcp_result(
            f'MCP search result for "{skill}"',
            result,
        ), 200

    except Exception as exc:
        return format_error(
            f"MCP search failed: {exc}"
        ), 200


@htmx_mode_bp.post("/htmx/mcp/listing")
def htmx_mcp_listing():
    if not mcp_is_enabled():
        return format_error(
            "MCP Mode is disabled."
        ), 200

    raw_listing_id = request.form.get(
        "listing_id",
        "",
    )

    try:
        listing_id = int(
            raw_listing_id
        )

        if listing_id <= 0:
            raise ValueError

    except (
        TypeError,
        ValueError,
    ):
        return format_error(
            "Listing ID must be a positive integer."
        ), 200

    try:
        result = get_listing(
            listing_id,
        )

        return format_mcp_result(
            f"MCP listing #{listing_id}",
            result,
        ), 200

    except Exception as exc:
        return format_error(
            f"MCP listing retrieval failed: {exc}"
        ), 200


@htmx_mode_bp.get("/htmx/rag/status")
def htmx_rag_status():
    enabled = rag_is_enabled()

    message = (
        "RAG Mode is enabled and configured for Student 2."
        if enabled
        else "RAG Mode is disabled."
    )

    return format_service_status(
        message,
        enabled,
    ), 200


@htmx_mode_bp.post("/htmx/rag/refresh")
def htmx_rag_refresh():
    if not rag_is_enabled():
        return format_error(
            "RAG Mode is disabled."
        ), 200

    try:
        result = refresh_corpus()

        return format_rag_refresh(
            result,
        ), 200

    except Exception as exc:
        return format_error(
            f"RAG corpus refresh failed: {exc}"
        ), 200


@htmx_mode_bp.post("/htmx/rag/retrieve")
def htmx_rag_retrieve():
    if not rag_is_enabled():
        return format_error(
            "RAG Mode is disabled."
        ), 200

    query = str(
        request.form.get(
            "query",
            "",
        )
    ).strip()

    if not query:
        return format_error(
            "A retrieval query is required."
        ), 200

    try:
        k = _parse_k(
            request.form.get("k")
        )

        result = retrieve_context(
            query,
            k,
        )

        return format_rag_retrieval(
            result,
        ), 200

    except ValueError as exc:
        return format_error(
            str(exc)
        ), 200

    except Exception as exc:
        return format_error(
            f"RAG retrieval failed: {exc}"
        ), 200


@htmx_mode_bp.post("/htmx/rag/answer")
def htmx_rag_answer():
    if not rag_is_enabled():
        return format_error(
            "RAG Mode is disabled."
        ), 200

    query = str(
        request.form.get(
            "query",
            "",
        )
    ).strip()

    if not query:
        return format_error(
            "A question is required."
        ), 200

    try:
        k = _parse_k(
            request.form.get("k")
        )

        result = answer_question(
            query,
            k,
        )

        return format_rag_answer(
            result,
        ), 200

    except ValueError as exc:
        return format_error(
            str(exc)
        ), 200

    except Exception as exc:
        return format_error(
            f"Grounded RAG answer failed: {exc}"
        ), 200
