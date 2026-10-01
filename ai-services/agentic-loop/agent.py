from __future__ import annotations

import argparse
import importlib
import json
import sys

from core.audit import append_audit
from core.runner import run_scenario


STUDENTS = (1, 2, 3, 4, 5)


def load_student_scenarios(
    student_number: int,
) -> dict:
    module = importlib.import_module(
        f"scenarios.student{student_number}"
    )

    scenarios = module.get_scenarios()

    if not isinstance(
        scenarios,
        dict,
    ):
        raise ValueError(
            f"Student {student_number} scenarios "
            "did not return a dictionary."
        )

    return scenarios


def selected_modes(
    mode: str,
) -> tuple[str, ...]:
    if mode == "all":
        return (
            "mcp",
            "rag",
        )

    return (
        mode,
    )


def describe_action(
    scenario: dict,
    mode: str,
) -> str:
    if mode == "mcp":
        return (
            f"call MCP tool "
            f"{scenario.get('tool', 'unknown')}"
        )

    return (
        f"call RAG "
        f"{scenario.get('action', 'unknown')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Shared Release 1 Plan -> Act -> "
            "Observe -> Adapt validation loop."
        )
    )

    parser.add_argument(
        "--mode",
        choices=(
            "mcp",
            "rag",
            "all",
        ),
        default="all",
        help="Validation mode to execute.",
    )

    parser.add_argument(
        "--students",
        nargs="*",
        type=int,
        default=list(STUDENTS),
        help=(
            "Student numbers to validate. "
            "Default: 1 2 3 4 5."
        ),
    )

    parser.add_argument(
        "--audit-path",
        default=None,
        help=(
            "Optional JSONL audit output path."
        ),
    )

    parser.add_argument(
        "--no-audit",
        action="store_true",
        help="Do not write JSONL audit evidence.",
    )

    args = parser.parse_args()

    invalid_students = [
        number
        for number in args.students
        if number not in STUDENTS
    ]

    if invalid_students:
        parser.error(
            "Invalid student numbers: "
            + ", ".join(
                str(number)
                for number in invalid_students
            )
        )

    print(
        "=" * 72
    )
    print(
        "RELEASE 1 SHARED AGENTIC VALIDATION LOOP"
    )
    print(
        "Workflow: Plan -> Act -> Observe -> Adapt"
    )
    print(
        f"Mode: {args.mode}"
    )
    print(
        "Students: "
        + ", ".join(
            str(number)
            for number in args.students
        )
    )
    print(
        "=" * 72
    )

    passed = 0
    failed = 0
    skipped = 0
    executed = 0

    for student_number in args.students:
        try:
            scenarios = load_student_scenarios(
                student_number
            )

        except Exception as exc:
            failed += 1

            print()
            print(
                f"[Student {student_number}] "
                "FAILED TO LOAD SCENARIOS"
            )
            print(
                f"  {type(exc).__name__}: {exc}"
            )

            continue

        for mode in selected_modes(
            args.mode
        ):
            cases = scenarios.get(
                mode,
                [],
            )

            if not cases:
                skipped += 1

                print()
                print(
                    f"[Student {student_number}] "
                    f"{mode.upper()} - SKIP"
                )
                print(
                    "  No validation scenarios "
                    "are currently defined."
                )

                continue

            for scenario in cases:
                executed += 1

                print()
                print(
                    "-" * 72
                )
                print(
                    f"{scenario.get('id', 'unknown')}"
                )

                print(
                    "PLAN:"
                )
                print(
                    "  "
                    + scenario.get(
                        "description",
                        "Run validation scenario.",
                    )
                )

                print(
                    "ACT:"
                )
                print(
                    "  "
                    + describe_action(
                        scenario,
                        mode,
                    )
                )

                result = run_scenario(
                    scenario,
                    mode,
                )

                print(
                    "OBSERVE:"
                )

                if result["passed"]:
                    passed += 1
                    print(
                        "  PASS"
                    )

                else:
                    failed += 1
                    print(
                        "  FAIL"
                    )

                    for error in result[
                        "errors"
                    ]:
                        print(
                            f"  - {error}"
                        )

                print(
                    "ADAPT:"
                )

                adaptation = result[
                    "adaptation"
                ]

                if adaptation == "not_required":
                    print(
                        "  No adaptation required."
                    )

                elif adaptation == "retry_succeeded":
                    print(
                        "  Initial observation failed; "
                        "one retry succeeded."
                    )

                elif adaptation == "retry_failed":
                    print(
                        "  Initial observation failed; "
                        "one retry was attempted and "
                        "also failed."
                    )

                else:
                    print(
                        "  No retry was attempted."
                    )

                print(
                    f"  Attempts: "
                    f"{result['attempts']}"
                )

                if not args.no_audit:
                    append_audit(
                        result,
                        args.audit_path,
                    )

    summary = {
        "type": "summary",
        "mode": args.mode,
        "students": args.students,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "skipped_mode_groups": skipped,
    }

    if not args.no_audit:
        audit_path = append_audit(
            summary,
            args.audit_path,
        )

    else:
        audit_path = None

    print()
    print(
        "=" * 72
    )
    print(
        "VALIDATION SUMMARY"
    )
    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    if audit_path:
        print(
            f"Audit evidence: {audit_path}"
        )

    print(
        "=" * 72
    )

    return (
        1
        if failed or skipped
        else 0
    )


if __name__ == "__main__":
    sys.exit(
        main()
    )
