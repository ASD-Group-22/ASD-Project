import importlib.util
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent

# Load service-specific local configuration before importing modules
# that read environment variables.
load_dotenv(BASE_DIR / ".env")

from adapters import AdapterError  # noqa: E402
from coordinator import (  # noqa: E402
    WorkflowError,
    apply_human_review,
    create_workflow,
    get_workflow,
)


app = Flask(__name__)


def _implemented_adapters() -> list[str]:
    implemented = []

    for student_number in range(1, 6):
        feature = f"student{student_number}"

        if importlib.util.find_spec(
            f"adapters.{feature}"
        ) is not None:
            implemented.append(
                feature
            )

    return implemented


def _json_body() -> dict[str, Any]:
    if not request.is_json:
        raise ValueError(
            "Request body must use application/json"
        )

    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "Request body must be a JSON object"
        )

    return payload


def _error_response(
    message: str,
    status_code: int,
):
    return (
        jsonify(
            {
                "error": message,
            }
        ),
        status_code,
    )


@app.get("/")
def service_info():
    return jsonify(
        {
            "service": "group-22-multi-agent-server",
            "status": "ok",
            "workflow": [
                "planner",
                "feature_evidence",
                "worker",
                "reviewer",
                "human_review",
            ],
            "implemented_adapters": _implemented_adapters(),
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "multi-agent-server",
            "implemented_adapters": _implemented_adapters(),
            "human_review_required": True,
        }
    )


@app.post("/workflows")
def start_workflow():
    try:
        payload = _json_body()

        workflow = create_workflow(
            feature=payload.get(
                "feature",
                "",
            ),
            task_type=payload.get(
                "task_type",
                "",
            ),
            user_request=payload.get(
                "user_request",
                "",
            ),
            context=payload.get(
                "context",
                {},
            ),
        )

        return (
            jsonify(
                workflow
            ),
            201,
        )

    except AdapterError as exc:
        return _error_response(
            str(exc),
            400,
        )

    except ValueError as exc:
        return _error_response(
            str(exc),
            400,
        )

    except WorkflowError as exc:
        return _error_response(
            str(exc),
            422,
        )


@app.get("/workflows/<workflow_id>")
def workflow_status(
    workflow_id: str,
):
    try:
        workflow = get_workflow(
            workflow_id
        )

        return jsonify(
            workflow
        )

    except WorkflowError as exc:
        status_code = (
            404
            if str(exc) == "Workflow not found"
            else 400
        )

        return _error_response(
            str(exc),
            status_code,
        )


@app.get("/workflows/<workflow_id>/history")
def workflow_history(
    workflow_id: str,
):
    try:
        workflow = get_workflow(
            workflow_id
        )

        return jsonify(
            {
                "workflow_id": workflow[
                    "workflow_id"
                ],
                "status": workflow[
                    "status"
                ],
                "history": workflow.get(
                    "history",
                    [],
                ),
            }
        )

    except WorkflowError as exc:
        status_code = (
            404
            if str(exc) == "Workflow not found"
            else 400
        )

        return _error_response(
            str(exc),
            status_code,
        )


@app.post("/workflows/<workflow_id>/human-review")
def human_review(
    workflow_id: str,
):
    try:
        payload = _json_body()

        workflow = apply_human_review(
            workflow_id,
            decision=payload.get(
                "decision",
                "",
            ),
            notes=payload.get(
                "notes"
            ),
            corrected_response=payload.get(
                "corrected_response"
            ),
        )

        return jsonify(
            workflow
        )

    except ValueError as exc:
        return _error_response(
            str(exc),
            400,
        )

    except WorkflowError as exc:
        status_code = (
            404
            if str(exc) == "Workflow not found"
            else 409
        )

        return _error_response(
            str(exc),
            status_code,
        )


if __name__ == "__main__":
    host = os.getenv(
        "MULTI_AGENT_HOST",
        "0.0.0.0",  # noqa: S104 - Docker backends must reach the local host service
    )

    port = int(
        os.getenv(
            "MULTI_AGENT_PORT",
            "5101",
        )
    )

    app.run(
        host=host,
        port=port,
        debug=False,
    )