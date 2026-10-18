from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo_path(relative_path: str) -> Path:
    return REPO_ROOT / relative_path


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _read_text(
    path: Path,
    max_chars: int = 12000,
) -> str:
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    if len(text) > max_chars:
        return text[:max_chars] + "\n...[truncated]"

    return text


def _unavailable(
    source_type: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "available": False,
        "source_type": source_type,
        "reason": reason,
    }


def _collect_multi_agent_workflow(
    scenario: dict,
) -> dict[str, Any]:
    review = scenario.get(
        "review",
        {},
    )

    workflow_dir = _repo_path(
        review.get(
            "workflow_dir",
            (
                "ai-services/multi-agent-server/"
                "runtime/workflows"
            ),
        )
    )

    feature = review.get(
        "feature",
        "student2",
    )

    if not workflow_dir.is_dir():
        return _unavailable(
            "multi_agent_workflow",
            (
                "Multi-Agent workflow directory "
                f"does not exist: {_relative(workflow_dir)}"
            ),
        )

    candidates = sorted(
        workflow_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    for path in candidates:
        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            continue

        if not isinstance(
            payload,
            dict,
        ):
            continue

        if (
            feature
            and payload.get("feature")
            != feature
        ):
            continue

        if payload.get("status") != "completed":
            continue

        human_review = payload.get(
            "human_review",
            {},
        )

        if not isinstance(
            human_review,
            dict,
        ):
            continue

        if (
            human_review.get("status")
            != "completed"
        ):
            continue

        evidence = payload.get(
            "evidence",
            {},
        )

        worker = payload.get(
            "worker",
            {},
        )

        reviewer = payload.get(
            "reviewer",
            {},
        )

        selected_references = set(
            worker.get(
                "result",
                {},
            ).get(
                "selected_references",
                [],
            )
        )

        allowed_references = set(
            evidence.get(
                "allowed_output_references",
                [],
            )
        )

        deterministic_checks = {
            "workflow_completed": (
                payload.get("status")
                == "completed"
            ),
            "planner_success": (
                payload.get(
                    "planner",
                    {},
                ).get("status")
                == "success"
            ),
            "worker_success": (
                worker.get("status")
                == "success"
            ),
            "reviewer_success": (
                reviewer.get("status")
                == "success"
            ),
            "human_review_completed": (
                human_review.get("status")
                == "completed"
            ),
            "worker_references_grounded": (
                selected_references
                <= allowed_references
            ),
        }

        compact_evidence = {
            "workflow_id": payload.get(
                "workflow_id"
            ),
            "feature": payload.get(
                "feature"
            ),
            "task_type": payload.get(
                "task_type"
            ),
            "user_request": payload.get(
                "user_request"
            ),
            "status": payload.get(
                "status"
            ),
            "planner": payload.get(
                "planner"
            ),
            "application_evidence": {
                "source": evidence.get(
                    "source"
                ),
                "requester": evidence.get(
                    "requester"
                ),
                "candidates": evidence.get(
                    "candidates"
                ),
                "allowed_output_references": (
                    evidence.get(
                        "allowed_output_references"
                    )
                ),
                "evidence_count": evidence.get(
                    "evidence_count"
                ),
            },
            "worker": worker,
            "reviewer": reviewer,
            "human_review": human_review,
            "final_response": payload.get(
                "final_response"
            ),
            "history": payload.get(
                "history",
                [],
            ),
            "deterministic_checks": (
                deterministic_checks
            ),
        }

        return {
            "available": True,
            "source_type": (
                "multi_agent_workflow"
            ),
            "source_path": _relative(path),
            "evidence": compact_evidence,
        }

    return _unavailable(
        "multi_agent_workflow",
        (
            "No completed Multi-Agent workflow "
            f"was found for feature {feature!r}."
        ),
    )


def _collect_report(
    scenario: dict,
    source_type: str,
) -> dict[str, Any]:
    review = scenario.get(
        "review",
        {},
    )

    primary_relative = review.get(
        "primary_path",
        "",
    )

    if not primary_relative:
        return _unavailable(
            source_type,
            "No primary report path was configured.",
        )

    primary_path = _repo_path(
        primary_relative
    )

    if not primary_path.is_file():
        return _unavailable(
            source_type,
            (
                "Required report does not exist: "
                f"{primary_relative}"
            ),
        )

    primary_text = _read_text(
        primary_path
    ).strip()

    if not primary_text:
        return _unavailable(
            source_type,
            (
                "Required report is empty: "
                f"{primary_relative}"
            ),
        )

    supplemental = []

    for relative_path in review.get(
        "supplemental_paths",
        [],
    ):
        path = _repo_path(
            relative_path
        )

        item = {
            "path": relative_path,
            "exists": path.is_file(),
            "non_empty": False,
        }

        if path.is_file():
            content = _read_text(
                path,
                max_chars=8000,
            )

            item["content"] = content
            item["non_empty"] = bool(
                content.strip()
            )

        supplemental.append(
            item
        )

    deterministic_checks = {
        "report_exists": primary_path.is_file(),
        "report_non_empty": bool(primary_text),
    }

    for item in supplemental:
        artifact_name = str(
            item["path"]
        ).replace(
            "\\",
            "/",
        )

        deterministic_checks[
            f"supplemental_exists:{artifact_name}"
        ] = item["exists"]

        deterministic_checks[
            f"supplemental_non_empty:{artifact_name}"
        ] = item["non_empty"]

    return {
        "available": True,
        "source_type": source_type,
        "source_path": primary_relative,
        "evidence": {
            "report": primary_text,
            "supplemental_artifacts": (
                supplemental
            ),
            "deterministic_checks": (
                deterministic_checks
            ),
        },
    }


def collect_evidence(
    scenario: dict,
    mode: str,
) -> dict[str, Any]:
    if mode == "multi-agent-review":
        return _collect_multi_agent_workflow(
            scenario
        )

    if mode == "testing-report-review":
        return _collect_report(
            scenario,
            "testing_report",
        )

    if mode == "cloud-deployment-review":
        return _collect_report(
            scenario,
            "cloud_deployment_report",
        )

    raise ValueError(
        f"Unsupported review mode: {mode}"
    )
