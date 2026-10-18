from __future__ import annotations

import json
import os
from typing import Any

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
).rstrip("/")

IMPLEMENTATION_MODEL = os.getenv(
    "AGENTIC_REVIEW_IMPLEMENTATION_MODEL",
    "qwen3:8b",
)

REVIEW_MODEL = os.getenv(
    "AGENTIC_REVIEW_MODEL",
    "llama3.1:8b",
)

CONNECT_TIMEOUT = float(
    os.getenv(
        "AGENTIC_REVIEW_CONNECT_TIMEOUT",
        "5",
    )
)

READ_TIMEOUT = float(
    os.getenv(
        "AGENTIC_REVIEW_READ_TIMEOUT",
        "240",
    )
)


def _chat_json(
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "stream": False,
            "think": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "options": {
                "temperature": 0,
                "num_predict": 1400,
            },
        },
        timeout=(
            CONNECT_TIMEOUT,
            READ_TIMEOUT,
        ),
    )

    response.raise_for_status()

    payload = response.json()

    content = (
        payload.get(
            "message",
            {},
        ).get(
            "content",
            "",
        )
    )

    if not content:
        raise ValueError(
            "Ollama returned an empty review."
        )

    parsed = json.loads(
        content
    )

    if not isinstance(
        parsed,
        dict,
    ):
        raise ValueError(
            "Ollama review was not a JSON object."
        )

    return parsed


def run_two_stage_review(
    title: str,
    description: str,
    evidence: dict,
) -> dict[str, Any]:
    evidence_json = json.dumps(
        evidence,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    implementation_prompt = f"""
Review Title:
{title}

Review Objective:
{description}

Evidence:
{evidence_json}

Assess only the supplied evidence.
Do not invent missing facts.

Return JSON with exactly these top-level fields:
- decision: one of pass, needs_attention, fail
- summary: concise evidence-based assessment
- strengths: list of supported strengths
- gaps: list of missing, weak, or risky areas
- evidence_used: list of evidence references used
"""

    implementation_review = _chat_json(
        IMPLEMENTATION_MODEL,
        (
            "You are the implementation assessment "
            "stage of a software validation loop. "
            "Use only supplied evidence."
        ),
        implementation_prompt,
    )

    reviewer_prompt = f"""
Review Title:
{title}

Original Evidence:
{evidence_json}

Implementation Assessment:
{json.dumps(
    implementation_review,
    indent=2,
    ensure_ascii=False,
    default=str,
)}

Validate whether the implementation assessment is
grounded in the supplied evidence.

Return JSON with exactly these top-level fields:
- decision: one of approve, revise, reject
- assessment_grounded: boolean
- issues: list of unsupported claims or missed risks
- recommendation: concise final review recommendation
"""

    reviewer_review = _chat_json(
        REVIEW_MODEL,
        (
            "You are the independent reviewer stage "
            "of a software validation loop. Check "
            "grounding, completeness, and unsupported "
            "claims."
        ),
        reviewer_prompt,
    )

    return {
        "implementation_model": (
            IMPLEMENTATION_MODEL
        ),
        "review_model": REVIEW_MODEL,
        "implementation_review": (
            implementation_review
        ),
        "reviewer_review": reviewer_review,
    }
