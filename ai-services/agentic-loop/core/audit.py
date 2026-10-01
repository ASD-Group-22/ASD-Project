from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_AUDIT_PATH = (
    Path(__file__).resolve().parents[1]
    / "evidence"
    / "agentic-validation.jsonl"
)


def now_iso() -> str:
    """Return a UTC ISO-8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


def get_audit_path(
    override: str | Path | None = None,
) -> Path:
    """Resolve the audit output path."""
    if override:
        return Path(override)

    configured = os.getenv(
        "AGENTIC_AUDIT_PATH",
        "",
    ).strip()

    if configured:
        return Path(configured)

    return DEFAULT_AUDIT_PATH


def append_audit(
    record: dict[str, Any],
    path: str | Path | None = None,
) -> Path:
    """Append one structured validation record as JSONL."""
    target = get_audit_path(path)
    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = dict(record)
    payload.setdefault(
        "timestamp",
        now_iso(),
    )

    with target.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                payload,
                ensure_ascii=False,
                default=str,
            )
        )
        handle.write("\n")

    return target
