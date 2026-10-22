"""Shared workflow coordinator with an optional feature-reviewer hook.

Adapters that expose only gather_evidence() use the existing shared reviewer.
The Student 3 adapter additionally exposes review_work(), so only Student 3
receives its specialised evidence-constrained review behaviour.
"""
from typing import Any
from uuid import uuid4

from adapters import load_adapter, normalize_feature
from agents.planner_agent import plan_workflow
from agents.reviewer_agent import review_work as review_with_shared_agent
from agents.worker_agent import perform_work
from workflow_store import (
    append_audit,
    append_history,
    load_workflow,
    now_iso,
    save_workflow,
)


class WorkflowError(RuntimeError):
    """Raised when a Multi-Agent workflow cannot be completed."""


HUMAN_DECISIONS = {"approve", "correct", "partial_accept", "reject"}


def _persist(workflow: dict[str, Any]) -> None:
    workflow["updated_at"] = now_iso()
    save_workflow(workflow)


def _review_with_feature_hook(
    adapter: Any,
    user_request: str,
    planner_result: dict[str, Any],
    evidence: dict[str, Any],
    worker_result: dict[str, Any],
) -> dict[str, Any]:
    """Call an adapter reviewer only when that adapter explicitly provides one.

    This is intentionally opt-in. Existing adapters do not implement
    review_work(), so their request path remains the original shared reviewer.
    """
    feature_reviewer = getattr(adapter, "review_work", None)
    if callable(feature_reviewer):
        result = feature_reviewer(user_request, planner_result, evidence, worker_result)
        if not isinstance(result, dict) or not isinstance(result.get("review"), dict):
            raise WorkflowError("Feature reviewer returned an invalid result")
        return result
    return review_with_shared_agent(user_request, planner_result, evidence, worker_result)


def _review_details(reviewer_result: dict[str, Any]) -> dict[str, Any]:
    review = reviewer_result.get("review", {})
    return review if isinstance(review, dict) else {}


def create_workflow(
    *,
    feature: str,
    task_type: str,
    user_request: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    normalized_feature = normalize_feature(feature)
    if not str(task_type or "").strip():
        raise WorkflowError("task_type is required")
    if not str(user_request or "").strip():
        raise WorkflowError("user_request is required")
    if not isinstance(context, dict):
        raise WorkflowError("context must be an object")

    workflow_id = str(uuid4())
    workflow = {
        "workflow_id": workflow_id,
        "feature": normalized_feature,
        "task_type": task_type,
        "user_request": user_request,
        "context": context,
        "status": "created",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "planner": None,
        "evidence": None,
        "worker": None,
        "reviewer": None,
        "human_review": {
            "status": "pending",
            "decision": None,
            "notes": None,
            "corrected_response": None,
            "reviewed_at": None,
        },
        "final_response": None,
        "history": [],
    }
    append_history(workflow, "created", "Multi-Agent workflow created.", {
        "feature": normalized_feature,
        "task_type": task_type,
    })
    append_audit("workflow_created", workflow_id, {
        "feature": normalized_feature,
        "task_type": task_type,
    })
    _persist(workflow)

    try:
        workflow["status"] = "planning"
        planner_result = plan_workflow(normalized_feature, task_type, user_request, context)
        workflow["planner"] = planner_result
        append_history(workflow, "planner", "Planner stage completed.", {
            "status": planner_result.get("status"),
            "model": planner_result.get("model"),
        })
        append_audit("planner_completed", workflow_id, {"status": planner_result.get("status")})
        _persist(workflow)

        workflow["status"] = "gathering_evidence"
        adapter = load_adapter(normalized_feature)
        evidence = adapter.gather_evidence(task_type, context)
        workflow["evidence"] = evidence
        append_history(workflow, "evidence", "Feature evidence retrieved through the owning backend/API.", {
            "source": evidence.get("source"),
            "evidence_count": evidence.get("evidence_count"),
        })
        append_audit("evidence_gathered", workflow_id, {
            "source": evidence.get("source"),
            "evidence_count": evidence.get("evidence_count"),
        })
        _persist(workflow)

        workflow["status"] = "working"
        worker_result = perform_work(user_request, planner_result, evidence)
        workflow["worker"] = worker_result
        append_history(workflow, "worker", "Worker stage completed using supplied application evidence.", {
            "status": worker_result.get("status"),
            "model": worker_result.get("model"),
        })
        append_audit("worker_completed", workflow_id, {"status": worker_result.get("status")})
        _persist(workflow)

        workflow["status"] = "reviewing"
        reviewer_result = _review_with_feature_hook(
            adapter,
            user_request,
            planner_result,
            evidence,
            worker_result,
        )
        workflow["reviewer"] = reviewer_result
        review = _review_details(reviewer_result)
        reviewer_details = {
            "status": reviewer_result.get("status"),
            "model": reviewer_result.get("model"),
            "decision": review.get("decision"),
            "mode": reviewer_result.get("reviewer_mode", "shared_reviewer"),
        }
        append_history(workflow, "reviewer", "Reviewer stage completed against the plan and evidence.", reviewer_details)
        append_audit("reviewer_completed", workflow_id, reviewer_details)

        workflow["status"] = "awaiting_human_review"
        append_history(workflow, "human_review", "Workflow is awaiting the required human review decision.")
        append_audit("human_review_requested", workflow_id)
        _persist(workflow)
        return workflow

    except Exception as exc:
        workflow["status"] = "failed"
        workflow["error"] = str(exc)
        append_history(workflow, "failed", "Multi-Agent workflow failed.", {"error": str(exc)})
        append_audit("workflow_failed", workflow_id, {"error": str(exc)})
        _persist(workflow)
        raise WorkflowError(str(exc)) from exc


def get_workflow(workflow_id: str) -> dict[str, Any]:
    workflow = load_workflow(workflow_id)
    if workflow is None:
        raise WorkflowError("Workflow not found")
    return workflow


def apply_human_review(
    workflow_id: str,
    *,
    decision: str,
    notes: str | None = None,
    corrected_response: str | None = None,
) -> dict[str, Any]:
    workflow = get_workflow(workflow_id)
    if workflow.get("status") != "awaiting_human_review":
        raise WorkflowError("Workflow is not awaiting human review")

    normalized_decision = str(decision or "").strip().lower()
    if normalized_decision not in HUMAN_DECISIONS:
        raise WorkflowError("decision must be approve, correct, partial_accept, or reject")
    if normalized_decision == "correct" and not str(corrected_response or "").strip():
        raise WorkflowError("corrected_response is required when decision=correct")

    worker_answer = workflow.get("worker", {}).get("result", {}).get("answer")
    if normalized_decision == "approve":
        final_response, final_status = worker_answer, "completed"
    elif normalized_decision == "correct":
        final_response, final_status = str(corrected_response).strip(), "completed"
    elif normalized_decision == "partial_accept":
        final_response = str(corrected_response or worker_answer or "").strip()
        final_status = "completed"
    else:
        final_response, final_status = None, "rejected"

    workflow["human_review"] = {
        "status": "completed",
        "decision": normalized_decision,
        "notes": str(notes).strip() if notes is not None else None,
        "corrected_response": str(corrected_response).strip() if corrected_response is not None else None,
        "reviewed_at": now_iso(),
    }
    workflow["final_response"] = final_response
    workflow["status"] = final_status
    append_history(workflow, "human_review", "Human review completed.", {"decision": normalized_decision})
    append_audit("human_review_completed", workflow_id, {"decision": normalized_decision})
    _persist(workflow)
    return workflow
