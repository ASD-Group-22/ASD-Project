import json
from typing import Any

from llm_client import (
    REVIEWER_MODEL,
    create_chat_completion,
    parse_json_object,
)


def _fallback_review(
    worker_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "decision": "needs_human_review",
        "plan_followed": False,
        "evidence_grounded": False,
        "issues": [
            "Automated Reviewer was unavailable."
        ],
        "recommendation": (
            "Human reviewer must inspect the Planner, "
            "application evidence, and Worker result."
        ),
    }


def review_work(
    user_request: str,
    planner_result: dict[str, Any],
    evidence: dict[str, Any],
    worker_result: dict[str, Any],
) -> dict[str, Any]:
    prompt = f"""
You are the Reviewer Agent in a shared university-management
Multi-Agent System.

Review the Worker output against BOTH the Planner result and
the supplied application evidence.

Return JSON only with this exact structure:
{{
  "decision": "approve|revise|reject",
  "plan_followed": true,
  "evidence_grounded": true,
  "issues": ["string"],
  "recommendation": "string"
}}

Rules:
- Check whether the Worker followed the Planner's plan.
- Check whether claims are grounded in supplied evidence.
- Check selected evidence references against allowed_output_references.
- Do not introduce new application facts.
- Reviewer approval does NOT replace final human review.

User Request:
{user_request}

Planner Result:
{json.dumps(planner_result, ensure_ascii=False, indent=2)}

Application Evidence:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

Worker Result:
{json.dumps(worker_result, ensure_ascii=False, indent=2)}
"""

    try:
        raw = create_chat_completion(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=REVIEWER_MODEL,
            max_tokens=500,
            temperature=0.0,
        )

        review = parse_json_object(
            raw
        )

        if review.get(
            "decision"
        ) not in {
            "approve",
            "revise",
            "reject",
        }:
            raise ValueError(
                "Reviewer returned an invalid decision"
            )

        if not isinstance(
            review.get("plan_followed"),
            bool,
        ):
            raise ValueError(
                "Reviewer plan_followed must be boolean"
            )

        if not isinstance(
            review.get("evidence_grounded"),
            bool,
        ):
            raise ValueError(
                "Reviewer evidence_grounded must be boolean"
            )

        if not isinstance(
            review.get("issues"),
            list,
        ):
            raise ValueError(
                "Reviewer issues must be a list"
            )

        if not isinstance(
            review.get("recommendation"),
            str,
        ):
            raise ValueError(
                "Reviewer recommendation must be a string"
            )

        return {
            "status": "success",
            "agent": "reviewer",
            "model": REVIEWER_MODEL,
            "review": review,
        }

    except Exception as exc:
        return {
            "status": "fallback",
            "agent": "reviewer",
            "model": REVIEWER_MODEL,
            "review": _fallback_review(
                worker_result
            ),
            "fallback_reason": str(exc),
        }