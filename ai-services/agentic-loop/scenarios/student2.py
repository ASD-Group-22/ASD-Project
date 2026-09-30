"""Student 2 - Skill Exchange agentic validation scenarios.

This module defines Student 2 validation scenarios for the single shared
Release 1 agentic loop.

The shared runner is responsible for executing these scenarios.

Student 2 owns this file.
"""


FEATURE = "student-2-skill-exchange"


def get_scenarios():
    """Return Student 2 MCP and RAG validation scenarios."""

    return {
        "mcp": [
            {
                "id": "student2_mcp_search_python",
                "feature": FEATURE,
                "description": (
                    "Search Skill Exchange listings for Python "
                    "through the Student 2 MCP tool."
                ),
                "action": "call_tool",
                "tool": "student2_search_skills",
                "arguments": {
                    "skill": "Python",
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "tool": "student2_search_skills",
                    "minimum_result_count": 1,
                    "listing_ids_include": [
                        1,
                        2,
                    ],
                },
            },
            {
                "id": "student2_mcp_get_listing_1",
                "feature": FEATURE,
                "description": (
                    "Retrieve seeded Skill Exchange listing 1 "
                    "through the Student 2 MCP tool."
                ),
                "action": "call_tool",
                "tool": "student2_get_listing",
                "arguments": {
                    "listing_id": 1,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "tool": "student2_get_listing",
                    "listing_id": 1,
                    "student_name": "Alice Nguyen",
                    "listing_status": "active",
                },
            },
            {
                "id": "student2_mcp_missing_listing",
                "feature": FEATURE,
                "description": (
                    "Verify clear MCP error behaviour for a "
                    "nonexistent Skill Exchange listing."
                ),
                "action": "call_tool",
                "tool": "student2_get_listing",
                "arguments": {
                    "listing_id": 99999,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "error",
                    "tool": "student2_get_listing",
                    "error": "Listing not found",
                },
            },
        ],
        "rag": [
            {
                "id": "student2_rag_retrieve_wants_java",
                "feature": FEATURE,
                "description": (
                    "Retrieve trusted Skill Exchange context "
                    "for a student who wants Java."
                ),
                "action": "retrieve",
                "request": {
                    "query": "Who wants Java?",
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "minimum_results": 1,
                    "first_listing_id": 4,
                    "first_student_name": "Daniel Kim",
                },
            },
            {
                "id": "student2_rag_answer_offers_python",
                "feature": FEATURE,
                "description": (
                    "Generate a grounded answer identifying "
                    "who offers Python."
                ),
                "action": "answer",
                "request": {
                    "query": "Who offers Python?",
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "answer_required": True,
                    "minimum_citations": 1,
                    "citation_listing_ids_include": [
                        1,
                    ],
                    "confidence_required": True,
                },
            },
            {
                "id": "student2_rag_insufficient_context",
                "feature": FEATURE,
                "description": (
                    "Verify unsupported questions do not "
                    "produce fabricated Skill Exchange answers."
                ),
                "action": "answer",
                "request": {
                    "query": (
                        "What are the parking fees on campus?"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "insufficient_context",
                    "answer": "Insufficient context.",
                    "citation_count": 0,
                    "confidence_category": "Insufficient",
                },
            },
        ],
    }
