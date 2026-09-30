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

    def _extract_between(
        value: str,
        start: str,
        end: str,
    ) -> str:
        if not value or start not in value:
            return ""

        remainder = value.split(
            start,
            1,
        )[1]

        if end and end in remainder:
            remainder = remainder.split(
                end,
                1,
            )[0]

        return remainder.strip().rstrip(".")

    cards = []

    for result in results:
        evidence = str(
            result.get("text") or ""
        )

        student_name = (
            result.get("student_name")
            or _extract_between(
                evidence,
                "Student: ",
                ". Student ID:",
            )
        )

        skill_offered = (
            result.get("skill_offered")
            or _extract_between(
                evidence,
                "Offers: ",
                ". Wants:",
            )
        )

        skill_wanted = (
            result.get("skill_wanted")
            or _extract_between(
                evidence,
                "Wants: ",
                ". Availability:",
            )
        )

        chunk_id = (
            result.get("chunk_id")
            or "-"
        )

        if not student_name:
            if "skill_exchange_catalog" in str(chunk_id):
                student_name = "Skill Exchange catalogue"
            else:
                student_name = "Retrieved context"

        offered_html = ""
        if skill_offered:
            offered_html = (
                '<p>Offered: '
                f'{_safe(skill_offered)}</p>'
            )

        wanted_html = ""
        if skill_wanted:
            wanted_html = (
                '<p>Wanted: '
                f'{_safe(skill_wanted)}</p>'
            )

        distance_html = ""
        if result.get("distance") is not None:
            distance_html = (
                '<p>Vector distance: '
                f'{_safe(result.get("distance"))}</p>'
            )

        cards.append(
            '<article class="citation-card">'
            f'<strong>Rank {_safe(result.get("rank", "-"))}</strong>'
            f'<p>Student: {_safe(student_name)}</p>'
            f'{offered_html}'
            f'{wanted_html}'
            f'<p>Evidence: {_safe(evidence or "-")}</p>'
            f'<p>Source: <code>{_safe(result.get("source_id") or "-")}</code></p>'
            f'<p>Chunk: <code>{_safe(chunk_id)}</code></p>'
            f'{distance_html}'
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
        source_id = str(
            citation.get("source_id") or ""
        )

        chunk_id = (
            citation.get("chunk_id")
            or "-"
        )

        listing_id = (
            citation.get("listing_id")
            or ""
        )

        if (
            not listing_id
            and source_id.startswith(
                "student-2:/skill-exchange/"
            )
        ):
            candidate_id = source_id.rsplit(
                "/",
                1,
            )[-1]

            if candidate_id.isdigit():
                listing_id = candidate_id

        listing_html = ""
        if listing_id:
            listing_html = (
                '<p>Listing: '
                f'{_safe(listing_id)}</p>'
            )

        citation_cards.append(
            '<article class="citation-card">'
            f'<strong>Citation {index}</strong>'
            f'<p>Source: <code>{_safe(source_id or "-")}</code></p>'
            f'{listing_html}'
            f'<p>Chunk: <code>{_safe(chunk_id)}</code></p>'
            f'<p>Authority: {_safe(citation.get("authority_tier") or "-")}</p>'
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

    answer_text = str(
        payload.get("answer") or ""
    ).strip()

    if answer_text.lower().startswith(
        "answer:"
    ):
        answer_text = answer_text.split(
            ":",
            1,
        )[1].strip()

    return (
        '<div class="htmx-result">'
        '<div class="rag-answer">'
        '<strong>Answer:</strong> '
        f'{_safe(answer_text)}'
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
