"""HTML fragment formatters used by the Student 2 HTMX presentation routes."""

from html import escape
import json


def _safe(value) -> str:
    if value is None:
        return ""
    return escape(str(value))


def format_service_status(message: str, enabled: bool = True) -> str:
    css_class = "status-ok" if enabled else "error"

    return (
        f'<p class="{css_class}">'
        f'{_safe(message)}'
        f'</p>'
    )


def format_error(message: str) -> str:
    return (
        '<p class="error">'
        f'{_safe(message)}'
        '</p>'
    )


def format_json_block(payload: dict) -> str:
    formatted = json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )

    return (
        '<pre class="rag-output">'
        f'{escape(formatted)}'
        '</pre>'
    )


def format_mcp_result(title: str, payload: dict) -> str:
    return (
        '<div class="htmx-result">'
        f'<h3>{_safe(title)}</h3>'
        f'{format_json_block(payload)}'
        '</div>'
    )


def format_rag_refresh(payload: dict) -> str:
    chunk_count = payload.get(
        "chunk_count",
        payload.get("chunks", "-"),
    )

    collection = payload.get(
        "collection",
        "-",
    )

    return (
        '<div class="htmx-result">'
        '<p><strong>Corpus refreshed successfully.</strong></p>'
        f'<p>Chunks: {_safe(chunk_count)}</p>'
        f'<p>Collection: {_safe(collection)}</p>'
        '</div>'
    )


def format_rag_retrieval(payload: dict) -> str:
    results = payload.get("results") or []

    if not results:
        return (
            '<div class="htmx-result">'
            '<p>No relevant context was retrieved.</p>'
            f'{format_json_block(payload)}'
            '</div>'
        )

    cards = []

    for result in results:
        cards.append(
            '<article class="citation-card">'
            f'<strong>Rank {_safe(result.get("rank", "-"))}</strong>'
            f'<p>Student: {_safe(result.get("student_name") or "Catalogue")}</p>'
            f'<p>Offered: {_safe(result.get("skill_offered") or "-")}</p>'
            f'<p>Wanted: {_safe(result.get("skill_wanted") or "-")}</p>'
            f'<p>Source: <code>{_safe(result.get("source_id") or "-")}</code></p>'
            f'<p>Relevance: {_safe(result.get("relevance") or "-")}</p>'
            '</article>'
        )

    detected_relation = payload.get(
        "detected_relation",
        "general",
    )

    return (
        '<div class="htmx-result">'
        '<div class="rag-meta">'
        '<span class="rag-badge">'
        f'Relation: {_safe(detected_relation)}'
        '</span>'
        '<span class="rag-badge">'
        f'Results: {_safe(len(results))}'
        '</span>'
        '</div>'
        + "".join(cards)
        + '<details>'
        '<summary>Raw Retrieval JSON</summary>'
        f'{format_json_block(payload)}'
        '</details>'
        '</div>'
    )


def format_rag_answer(payload: dict) -> str:
    citations = payload.get("citations") or []

    citation_cards = []

    for index, citation in enumerate(
        citations,
        start=1,
    ):
        citation_cards.append(
            '<article class="citation-card">'
            f'<strong>Citation {index}</strong>'
            f'<p>Source: <code>{_safe(citation.get("source_id") or "-")}</code></p>'
            f'<p>Listing: {_safe(citation.get("listing_id") or "-")}</p>'
            f'<p>Authority: {_safe(citation.get("authority_tier") or "-")}</p>'
            f'<p>Relevance: {_safe(citation.get("relevance") or "-")}</p>'
            '</article>'
        )

    if not citation_cards:
        citation_html = "<p>No citations were returned.</p>"
    else:
        citation_html = "".join(citation_cards)

    retrieval_summary = (
        payload.get("retrieval_summary")
        or {}
    )

    return (
        '<div class="htmx-result">'
        '<div class="rag-answer">'
        '<strong>Answer:</strong> '
        f'{_safe(payload.get("answer") or "")}'
        '</div>'
        '<div class="rag-meta">'
        '<span class="rag-badge">'
        f'Status: {_safe(payload.get("status") or "-")}'
        '</span>'
        '<span class="rag-badge">'
        f'Confidence: {_safe(payload.get("confidence_category") or "-")}'
        '</span>'
        '<span class="rag-badge">'
        f'Retrieved: {_safe(retrieval_summary.get("retrieved_count") or 0)}'
        '</span>'
        '</div>'
        '<h3>Citations</h3>'
        f'{citation_html}'
        '<details>'
        '<summary>Raw RAG JSON</summary>'
        f'{format_json_block(payload)}'
        '</details>'
        '</div>'
    )
