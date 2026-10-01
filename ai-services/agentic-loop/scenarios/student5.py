"""Student 5 - AI Campus Space Finder agentic validation scenarios.

Feature-owned scenarios executed by the single shared Release 1
Plan -> Act -> Observe -> Adapt validation loop.
"""

FEATURE = "student-5-campus-space-finder"


def get_scenarios():
    """Return Student 5 MCP and RAG validation scenarios."""

    return {
        "mcp": [
            {
                "id": "student5_mcp_find_spaces",
                "feature": FEATURE,
                "description": (
                    "Find stored campus spaces through the "
                    "shared Student 5 MCP tool."
                ),
                "action": "call_tool",
                "tool": "student5_find_campus_spaces",
                "arguments": {
                    "required_facilities": [
                        "Whiteboards",
                    ],
                    "limit": 3,
                },
                "expected": {
                    "minimum_result_count": 1,
                },
            },
        ],
        "rag": [
            {
                "id": "student5_rag_retrieve_feature_boundary",
                "feature": FEATURE,
                "description": (
                    "Retrieve trusted Student 5 feature "
                    "boundary context."
                ),
                "action": "retrieve",
                "request": {
                    "query": (
                        "AI Campus Space Finder login booking "
                        "live occupancy availability"
                    ),
                    "k": 2,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "minimum_results": 1,
                    "source_prefix": "student5-",
                },
            },
            {
                "id": "student5_rag_grounded_feature_boundary",
                "feature": FEATURE,
                "description": (
                    "Generate a grounded answer describing "
                    "what the Campus Space Finder does not provide."
                ),
                "action": "answer",
                "request": {
                    "query": (
                        "What does the AI Campus Space Finder "
                        "not provide?"
                    ),
                    "k": 2,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "answer_required": True,
                    "minimum_citations": 1,
                    "citation_source_prefix": "student5-",
                    "confidence_required": True,
                },
            },
            {
                "id": "student5_rag_insufficient_context",
                "feature": FEATURE,
                "description": (
                    "Verify an unsupported question does not "
                    "produce fabricated campus-space information."
                ),
                "action": "answer",
                "request": {
                    "query": (
                        "What are the current helicopter parking "
                        "prices on Mars?"
                    ),
                    "k": 2,
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
