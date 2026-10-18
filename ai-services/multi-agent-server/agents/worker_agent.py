import json
from typing import Any

from llm_client import (
    WORKER_MODEL,
    create_chat_completion,
    parse_json_object,
)


def _fallback_result(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    references = list(
        evidence.get(
            "allowed_output_references",
            [],
        )
    )

    return {
        "answer": (
            "The AI Worker was unavailable. "
            "The supplied application evidence remains available "
            "for Reviewer and human inspection."
        ),
        "selected_references": references,
        "limitations": [
            "Worker model output was unavailable.",
            "No additional facts were generated.",
        ],
    }


def perform_work(
    user_request: str,
    planner_result: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    prompt = f"""
You are the Worker Agent in a shared university-management
Multi-Agent System.

Perform the requested task using ONLY the supplied application evidence.

Return JSON only with this exact structure:
{{
  "answer": "string",
  "selected_references": ["reference_id"],
  "limitations": ["string"]
}}

Rules:
- Follow the Planner's plan.
- Use only supplied evidence.
- Do not invent students, projects, skills, spaces, IDs, or other records.
- selected_references may contain ONLY reference_id values present in
  allowed_output_references.
- If there is insufficient evidence, say so rather than inventing an answer.
- Keep the answer concise and suitable for later human review.

User Request:
{user_request}

Planner Result:
{json.dumps(planner_result, ensure_ascii=False, indent=2)}

Application Evidence:
{json.dumps(evidence, ensure_ascii=False, indent=2)}
"""

    try:
        raw = create_chat_completion(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=WORKER_MODEL,
            max_tokens=650,
            temperature=0.1,
        )

        result = parse_json_object(
            raw
        )

        if not isinstance(
            result.get("answer"),
            str,
        ):
            raise ValueError(
                "Worker output is missing answer"
            )

        references = result.get(
            "selected_references"
        )

        if not isinstance(
            references,
            list,
        ):
            raise ValueError(
                "Worker output is missing selected_references"
            )

        allowed = set(
            evidence.get(
                "allowed_output_references",
                [],
            )
        )

        unsupported = [
            reference
            for reference in references
            if reference not in allowed
        ]

        if unsupported:
            raise ValueError(
                "Worker selected unsupported evidence references: "
                + ", ".join(
                    map(
                        str,
                        unsupported,
                    )
                )
            )

        limitations = result.get(
            "limitations",
            [],
        )

        if not isinstance(
            limitations,
            list,
        ):
            raise ValueError(
                "Worker limitations must be a list"
            )

        return {
            "status": "success",
            "agent": "worker",
            "model": WORKER_MODEL,
            "result": result,
        }

    except Exception as exc:
        return {
            "status": "fallback",
            "agent": "worker",
            "model": WORKER_MODEL,
            "result": _fallback_result(
                evidence
            ),
            "fallback_reason": str(exc),
        }