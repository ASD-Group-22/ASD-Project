import json
from typing import Any

from llm_client import (
    PLANNER_MODEL,
    create_chat_completion,
    parse_json_object,
)


def _fallback_plan(
    feature: str,
    task_type: str,
    user_request: str,
) -> dict[str, Any]:
    return {
        "objective": user_request,
        "feature": feature,
        "task_type": task_type,
        "steps": [
            "Identify the feature-specific evidence required for the task.",
            "Use only evidence supplied by the feature adapter.",
            "Produce an evidence-backed result for independent review.",
        ],
        "required_evidence": [
            "Authoritative application evidence from the owning feature backend API"
        ],
        "constraints": [
            "Do not invent application records.",
            "Do not access feature databases directly.",
            "Require Reviewer and human review before completion.",
        ],
    }


def plan_workflow(
    feature: str,
    task_type: str,
    user_request: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    prompt = f"""
You are the Planner Agent in a shared university-management
Multi-Agent System.

Create a concise execution plan for the requested feature task.

Return JSON only with this exact top-level structure:
{{
  "objective": "string",
  "feature": "string",
  "task_type": "string",
  "steps": ["string"],
  "required_evidence": ["string"],
  "constraints": ["string"]
}}

Rules:
- Do not perform the task yourself.
- Do not invent records or evidence.
- Evidence must come from the owning feature backend/API.
- The Worker must use only supplied evidence.
- The Reviewer must check the Worker result against the plan and evidence.
- Human review is required before final completion.

Feature:
{feature}

Task Type:
{task_type}

User Request:
{user_request}

Request Context:
{json.dumps(context, ensure_ascii=False, indent=2)}
"""

    try:
        raw = create_chat_completion(
            [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=PLANNER_MODEL,
            max_tokens=450,
            temperature=0.1,
        )

        plan = parse_json_object(
            raw
        )

        required_fields = {
            "objective",
            "feature",
            "task_type",
            "steps",
            "required_evidence",
            "constraints",
        }

        if not required_fields.issubset(
            plan
        ):
            raise ValueError(
                "Planner output is missing required fields"
            )

        return {
            "status": "success",
            "agent": "planner",
            "model": PLANNER_MODEL,
            "plan": plan,
        }

    except Exception as exc:
        return {
            "status": "fallback",
            "agent": "planner",
            "model": PLANNER_MODEL,
            "plan": _fallback_plan(
                feature,
                task_type,
                user_request,
            ),
            "fallback_reason": str(exc),
        }