from __future__ import annotations

import asyncio
import json
import os
import re
import time
from typing import Any

import requests
from mcp import Client

from core.review_runner import REVIEW_MODES, execute_review_once


MCP_URL = os.getenv(
    "MCP_URL",
    "http://localhost:5100/mcp",
).rstrip("/")

RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL",
    "http://localhost:5003",
).rstrip("/")

RAG_CONNECT_TIMEOUT = float(
    os.getenv(
        "AGENTIC_RAG_CONNECT_TIMEOUT",
        "5",
    )
)

RAG_READ_TIMEOUT = float(
    os.getenv(
        "AGENTIC_RAG_READ_TIMEOUT",
        "180",
    )
)


def _decode_mcp_result(result: Any) -> dict:
    """Decode an MCP SDK tool response into a dictionary."""
    if getattr(
        result,
        "is_error",
        False,
    ):
        raise RuntimeError(
            "MCP tool returned an error"
        )

    structured = getattr(
        result,
        "structured_content",
        None,
    )

    if isinstance(
        structured,
        dict,
    ):
        return structured

    for item in getattr(
        result,
        "content",
        [],
    ):
        text = getattr(
            item,
            "text",
            None,
        )

        if not text:
            continue

        try:
            payload = json.loads(text)

        except json.JSONDecodeError:
            continue

        if isinstance(
            payload,
            dict,
        ):
            return payload

    raise ValueError(
        "MCP response did not contain a valid JSON object"
    )


async def _call_mcp_tool_async(
    tool_name: str,
    arguments: dict,
) -> dict:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(
            tool_name,
            arguments,
        )

        return _decode_mcp_result(
            result
        )


def call_mcp_tool(
    tool_name: str,
    arguments: dict,
) -> dict:
    """Call one tool on the shared local MCP server."""
    return asyncio.run(
        _call_mcp_tool_async(
            tool_name,
            arguments,
        )
    )


def call_rag(
    action: str,
    request: dict,
) -> dict:
    """Call one operation on the shared local RAG HTTP server."""
    paths = {
        "retrieve": "/retrieve",
        "answer": "/answer",
        "refresh": "/refresh",
    }

    if action not in paths:
        raise ValueError(
            f"Unsupported RAG action: {action}"
        )

    response = requests.post(
        f"{RAG_SERVICE_URL}{paths[action]}",
        json=request,
        timeout=(
            RAG_CONNECT_TIMEOUT,
            RAG_READ_TIMEOUT,
        ),
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "RAG response was not a JSON object"
        )

    return payload


def _listing_id_from_result(
    result: dict,
) -> int | None:
    """Extract a Skill Exchange listing ID from a RAG result."""
    direct = result.get(
        "listing_id"
    )

    try:
        if direct is not None:
            return int(direct)

    except (
        TypeError,
        ValueError,
    ):
        pass

    source_id = str(
        result.get(
            "source_id",
            "",
        )
    )

    match = re.search(
        r"/skill-exchange/(\d+)",
        source_id,
    )

    if match:
        return int(
            match.group(1)
        )

    text = str(
        result.get(
            "text",
            "",
        )
    )

    match = re.search(
        r"Listing ID:\s*(\d+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return int(
            match.group(1)
        )

    return None


def _student_name_from_result(
    result: dict,
) -> str | None:
    direct = result.get(
        "student_name"
    )

    if direct:
        return str(
            direct
        ).strip()

    text = str(
        result.get(
            "text",
            "",
        )
    )

    match = re.search(
        r"Student:\s*([^.;\n]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


def _first_listing_result(
    results: list,
) -> dict | None:
    """Return the first retrieved result representing a listing."""
    for result in results:
        if not isinstance(
            result,
            dict,
        ):
            continue

        if _listing_id_from_result(
            result
        ) is not None:
            return result

    return None


def _citation_listing_ids(
    citations: list,
) -> set[int]:
    found: set[int] = set()

    for citation in citations:
        if not isinstance(
            citation,
            dict,
        ):
            continue

        parsed = _listing_id_from_result(
            citation
        )

        if parsed is not None:
            found.add(parsed)

    return found


def evaluate_expected(
    scenario: dict,
    data: dict,
) -> list[str]:
    """Return validation failures for one scenario response."""
    expected = scenario.get(
        "expected",
        {},
    )

    failures: list[str] = []

    if "success" in expected:
        actual_success = data.get(
            "success"
        )

        if actual_success != expected["success"]:
            failures.append(
                "Expected success "
                f"{expected['success']!r}, got "
                f"{actual_success!r}."
            )

    profile = data.get(
        "profile",
        {},
    )

    if not isinstance(
        profile,
        dict,
    ):
        profile = {}

    if "profile_id" in expected:
        actual_profile_id = data.get(
            "profile_id",
            profile.get(
                "profile_id"
            ),
        )

        if (
            actual_profile_id
            != expected["profile_id"]
        ):
            failures.append(
                "Unexpected profile ID. "
                f"Expected {expected['profile_id']}, "
                f"got {actual_profile_id}."
            )

    if "profile_student_id" in expected:
        actual_student_id = profile.get(
            "student_id"
        )

        if (
            actual_student_id
            != expected["profile_student_id"]
        ):
            failures.append(
                "Unexpected profile student ID. "
                f"Expected "
                f"{expected['profile_student_id']}, "
                f"got {actual_student_id}."
            )

    required_skills = expected.get(
        "profile_skills_include"
    )

    if required_skills:
        skills = profile.get(
            "skills",
            [],
        )

        if not isinstance(
            skills,
            list,
        ):
            skills = []

        actual_skill_names = {
            item.get(
                "skill_name"
            )
            for item in skills
            if isinstance(
                item,
                dict,
            )
        }

        missing_skills = set(
            required_skills
        ) - actual_skill_names

        if missing_skills:
            failures.append(
                "Missing expected profile skills: "
                f"{sorted(missing_skills)}."
            )

    expected_status = expected.get(
        "status"
    )

    if (
        expected_status is not None
        and data.get("status")
        != expected_status
    ):
        failures.append(
            "Expected status "
            f"{expected_status!r}, got "
            f"{data.get('status')!r}."
        )

    expected_tool = expected.get(
        "tool"
    )

    if (
        expected_tool is not None
        and data.get("tool")
        != expected_tool
    ):
        failures.append(
            "Expected tool "
            f"{expected_tool!r}, got "
            f"{data.get('tool')!r}."
        )

    minimum_result_count = expected.get(
        "minimum_result_count"
    )

    if minimum_result_count is not None:
        count = data.get(
            "result_count"
        )

        if count is None:
            count = data.get(
                "count"
            )

        if count is None:
            listings = data.get(
                "listings"
            )

            if isinstance(
                listings,
                list,
            ):
                count = len(
                    listings
                )

        if count is None:
            matches = data.get(
                "matches"
            )

            if isinstance(
                matches,
                list,
            ):
                count = len(
                    matches
                )

        if count is None:
            count = 0

        if int(count or 0) < int(
            minimum_result_count
        ):
            failures.append(
                "Expected at least "
                f"{minimum_result_count} MCP results, "
                f"got {count}."
            )

    required_listing_ids = expected.get(
        "listing_ids_include"
    )

    if required_listing_ids:
        actual_ids = {
            item.get("listing_id")
            for item in data.get(
                "listings",
                [],
            )
            if isinstance(
                item,
                dict,
            )
        }

        missing = set(
            required_listing_ids
        ) - actual_ids

        if missing:
            failures.append(
                "Missing expected listing IDs: "
                f"{sorted(missing)}."
            )

    listing = data.get(
        "listing"
    )

    if not isinstance(
        listing,
        dict,
    ):
        listing = data

    if (
        "listing_id" in expected
        and listing.get("listing_id")
        != expected["listing_id"]
    ):
        failures.append(
            "Unexpected listing ID."
        )

    if (
        "student_name" in expected
        and listing.get("student_name")
        != expected["student_name"]
    ):
        failures.append(
            "Unexpected student name."
        )

    if (
        "listing_status" in expected
        and listing.get("status")
        != expected["listing_status"]
    ):
        failures.append(
            "Unexpected listing status."
        )

    if (
        "error" in expected
        and data.get("error")
        != expected["error"]
    ):
        failures.append(
            "Expected error "
            f"{expected['error']!r}, got "
            f"{data.get('error')!r}."
        )

    results = data.get(
        "results",
        [],
    )

    if not isinstance(
        results,
        list,
    ):
        results = []

    minimum_results = expected.get(
        "minimum_results"
    )

    if (
        minimum_results is not None
        and len(results)
        < int(minimum_results)
    ):
        failures.append(
            "Expected at least "
            f"{minimum_results} RAG results, "
            f"got {len(results)}."
        )

    if (
        "source_prefix" in expected
        and not any(
            isinstance(result, dict)
            and str(
                result.get(
                    "source_id",
                    "",
                )
            ).startswith(
                expected["source_prefix"]
            )
            for result in results
        )
    ):
        failures.append(
            "No retrieved result matched source prefix "
            f"{expected['source_prefix']!r}."
        )

    listing_result = _first_listing_result(
        results
    )

    if "first_listing_id" in expected:
        actual_listing_id = (
            _listing_id_from_result(
                listing_result
            )
            if listing_result
            else None
        )

        if (
            actual_listing_id
            != expected["first_listing_id"]
        ):
            failures.append(
                "Expected first listing ID "
                f"{expected['first_listing_id']}, "
                f"got {actual_listing_id}."
            )

    if "first_student_name" in expected:
        actual_student_name = (
            _student_name_from_result(
                listing_result
            )
            if listing_result
            else None
        )

        if (
            actual_student_name
            != expected["first_student_name"]
        ):
            failures.append(
                "Expected first listing student "
                f"{expected['first_student_name']!r}, "
                f"got {actual_student_name!r}."
            )

    answer = str(
        data.get(
            "answer",
            "",
        )
    ).strip()

    if (
        expected.get(
            "answer_required"
        )
        and not answer
    ):
        failures.append(
            "Grounded answer is missing."
        )

    if (
        "answer" in expected
        and answer
        != str(
            expected["answer"]
        ).strip()
    ):
        failures.append(
            "Unexpected answer text."
        )

    citations = data.get(
        "citations",
        [],
    )

    if not isinstance(
        citations,
        list,
    ):
        citations = []

    minimum_citations = expected.get(
        "minimum_citations"
    )

    if (
        minimum_citations is not None
        and len(citations)
        < int(minimum_citations)
    ):
        failures.append(
            "Expected at least "
            f"{minimum_citations} citations, "
            f"got {len(citations)}."
        )

    if "citation_count" in expected:
        if (
            len(citations)
            != int(
                expected["citation_count"]
            )
        ):
            failures.append(
                "Expected citation count "
                f"{expected['citation_count']}, "
                f"got {len(citations)}."
            )

    required_citation_ids = expected.get(
        "citation_listing_ids_include"
    )

    if required_citation_ids:
        actual_ids = _citation_listing_ids(
            citations
        )

        missing = set(
            required_citation_ids
        ) - actual_ids

        if missing:
            failures.append(
                "Missing citation listing IDs: "
                f"{sorted(missing)}."
            )

    citation_prefix = expected.get(
        "citation_source_prefix"
    )

    if citation_prefix:
        if not any(
            isinstance(
                citation,
                dict,
            )
            and str(
                citation.get(
                    "source_id",
                    "",
                )
            ).startswith(
                citation_prefix
            )
            for citation in citations
        ):
            failures.append(
                "No citation matched source prefix "
                f"{citation_prefix!r}."
            )

    confidence = data.get(
        "confidence_category"
    )

    if expected.get(
        "confidence_required"
    ):
        if confidence not in {
            "High",
            "Medium",
            "Low",
        }:
            failures.append(
                "A valid confidence category "
                "was not returned."
            )

    if (
        "confidence_category" in expected
        and confidence
        != expected["confidence_category"]
    ):
        failures.append(
            "Expected confidence category "
            f"{expected['confidence_category']!r}, "
            f"got {confidence!r}."
        )

    return failures


def execute_once(
    scenario: dict,
    mode: str,
) -> dict:
    """Execute one shared agentic-loop scenario once."""
    try:
        if mode in REVIEW_MODES:
            return execute_review_once(
                scenario,
                mode,
            )

        if mode == "mcp":
            data = call_mcp_tool(
                scenario["tool"],
                scenario.get(
                    "arguments",
                    {},
                ),
            )

        elif mode == "rag":
            data = call_rag(
                scenario["action"],
                scenario.get(
                    "request",
                    {},
                ),
            )

        else:
            raise ValueError(
                f"Unsupported validation mode: {mode}"
            )

        failures = evaluate_expected(
            scenario,
            data,
        )

        return {
            "passed": not failures,
            "errors": failures,
            "response": data,
        }

    except Exception as exc:
        return {
            "passed": False,
            "errors": [
                f"{type(exc).__name__}: {exc}"
            ],
            "response": {
                "status": "error",
                "error": str(exc),
            },
        }


def run_scenario(
    scenario: dict,
    mode: str,
    retry_once: bool = True,
) -> dict:
    """Execute and observe one scenario, then adapt once if required."""
    first = execute_once(
        scenario,
        mode,
    )

    result = {
        "id": scenario.get(
            "id",
            "unknown",
        ),
        "feature": scenario.get(
            "feature",
            "unknown",
        ),
        "description": scenario.get(
            "description",
            "",
        ),
        "mode": mode,
        "passed": first["passed"],
        "errors": first["errors"],
        "response": first["response"],
        "attempts": 1,
        "adaptation": (
            "not_required"
            if first["passed"]
            else "not_attempted"
        ),
    }

    if (
        first["passed"]
        or not retry_once
    ):
        return result

    time.sleep(1)

    second = execute_once(
        scenario,
        mode,
    )

    result.update(
        {
            "passed": second["passed"],
            "errors": second["errors"],
            "response": second["response"],
            "attempts": 2,
            "adaptation": (
                "retry_succeeded"
                if second["passed"]
                else "retry_failed"
            ),
            "initial_errors": first[
                "errors"
            ],
        }
    )

    return result
