from __future__ import annotations

from reviews.collectors import collect_evidence
from reviews.llm_review import run_two_stage_review


REVIEW_MODES = (
    "multi-agent-review",
    "testing-report-review",
    "cloud-deployment-review",
)


def execute_review_once(
    scenario: dict,
    mode: str,
) -> dict:
    """Execute one Release 2 evidence-review scenario."""
    collected = collect_evidence(
        scenario,
        mode,
    )

    if not collected.get(
        "available",
        False,
    ):
        reason = collected.get(
            "reason",
            "Required review evidence is unavailable.",
        )

        return {
            "passed": False,
            "errors": [reason],
            "response": {
                "status": "evidence_unavailable",
                "mode": mode,
                "source_type": collected.get(
                    "source_type"
                ),
                "reason": reason,
            },
        }

    evidence = collected.get(
        "evidence",
        {},
    )

    review = run_two_stage_review(
        scenario.get(
            "review_title",
            scenario.get(
                "id",
                mode,
            ),
        ),
        scenario.get(
            "description",
            "",
        ),
        evidence,
    )

    implementation_review = review.get(
        "implementation_review",
        {},
    )

    reviewer_review = review.get(
        "reviewer_review",
        {},
    )

    failures = []

    if (
        implementation_review.get("decision")
        != "pass"
    ):
        failures.append(
            "Implementation assessment did not return pass."
        )

    if (
        reviewer_review.get("decision")
        != "approve"
    ):
        failures.append(
            "Independent reviewer did not approve the assessment."
        )

    if (
        reviewer_review.get(
            "assessment_grounded"
        )
        is not True
    ):
        failures.append(
            "Independent reviewer did not confirm evidence grounding."
        )

    deterministic_checks = evidence.get(
        "deterministic_checks",
        {},
    )

    failed_checks = [
        name
        for name, passed in deterministic_checks.items()
        if passed is not True
    ]

    if failed_checks:
        failures.append(
            "Deterministic evidence checks failed: "
            + ", ".join(failed_checks)
        )

    response = {
        "status": (
            "success"
            if not failures
            else "review_failed"
        ),
        "mode": mode,
        "source_type": collected.get(
            "source_type"
        ),
        "source_path": collected.get(
            "source_path"
        ),
        "evidence": evidence,
        **review,
        "validation": {
            "passed": not failures,
            "failed_deterministic_checks": (
                failed_checks
            ),
        },
    }

    return {
        "passed": not failures,
        "errors": failures,
        "response": response,
    }
