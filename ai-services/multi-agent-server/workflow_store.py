import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID


BASE_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(
    os.getenv(
        "MULTI_AGENT_RUNTIME_DIR",
        str(BASE_DIR / "runtime"),
    )
)
WORKFLOW_DIR = RUNTIME_DIR / "workflows"
AUDIT_PATH = RUNTIME_DIR / "coordination-audit.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_runtime() -> None:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)


def _validated_workflow_id(workflow_id: str) -> str:
    return str(UUID(str(workflow_id)))


def _workflow_path(workflow_id: str) -> Path:
    safe_id = _validated_workflow_id(workflow_id)
    return WORKFLOW_DIR / f"{safe_id}.json"


def save_workflow(workflow: dict[str, Any]) -> None:
    _ensure_runtime()

    workflow_id = _validated_workflow_id(
        workflow["workflow_id"]
    )
    target = _workflow_path(workflow_id)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=WORKFLOW_DIR,
        delete=False,
        suffix=".tmp",
    ) as handle:
        json.dump(
            workflow,
            handle,
            ensure_ascii=False,
            indent=2,
        )
        temp_path = Path(handle.name)

    temp_path.replace(target)


def load_workflow(
    workflow_id: str,
) -> dict[str, Any] | None:
    try:
        path = _workflow_path(workflow_id)
    except ValueError:
        return None

    if not path.exists():
        return None

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def append_history(
    workflow: dict[str, Any],
    stage: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> None:
    workflow.setdefault(
        "history",
        [],
    ).append(
        {
            "timestamp": now_iso(),
            "stage": stage,
            "message": message,
            "details": details or {},
        }
    )


def append_audit(
    event: str,
    workflow_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    _ensure_runtime()

    record = {
        "timestamp": now_iso(),
        "workflow_id": workflow_id,
        "event": event,
        "details": details or {},
    }

    with AUDIT_PATH.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )