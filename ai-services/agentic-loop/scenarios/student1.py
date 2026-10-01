"""Student 1 - Project Management agentic validation scenarios.

Feature-owned scenarios executed by the single shared Release 1
Plan -> Act -> Observe -> Adapt validation loop.
"""


FEATURE = "student-1-project-management"


def get_scenarios():
    """Return Student 1 MCP and RAG validation scenarios."""

    return {
        "mcp": [
            {
                "id": "student1_mcp_project_6",
                "feature": FEATURE,
                "description": (
                    "Retrieve Project Management project 6 "
                    "through the shared Student 1 MCP tool."
                ),
                "action": "call_tool",
                "tool": "project_details",
                "arguments": {
                    "project_id": 6,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "tool": "project_details",
                },
            },
            {
                "id": "student1_mcp_project_6_tasks",
                "feature": FEATURE,
                "description": (
                    "Retrieve the tasks recorded for Project "
                    "Management project 6 through MCP."
                ),
                "action": "call_tool",
                "tool": "project_tasks",
                "arguments": {
                    "project_id": 6,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "tool": "project_tasks",
                },
            },
            {
                "id": "student1_mcp_invalid_project",
                "feature": FEATURE,
                "description": (
                    "Verify Student 1 MCP rejects an invalid "
                    "project ID clearly."
                ),
                "action": "call_tool",
                "tool": "project_details",
                "arguments": {
                    "project_id": 0,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "error",
                    "tool": "project_details",
                    "error": (
                        "project_id must be a positive integer"
                    ),
                },
            },
        ],
        "rag": [
            {
                "id": "student1_rag_retrieve_project_6",
                "feature": FEATURE,
                "description": (
                    "Retrieve trusted Project Management context "
                    "for project 6."
                ),
                "action": "retrieve",
                "request": {
                    "query": (
                        "Project Management Application project 6 "
                        "tasks"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "minimum_results": 1,
                    "source_prefix": "student1:backend-api:",
                },
            },
            {
                "id": "student1_rag_grounded_project_6",
                "feature": FEATURE,
                "description": (
                    "Generate a grounded answer describing the "
                    "tasks for Project Management project 6."
                ),
                "action": "answer",
                "request": {
                    "query": (
                        "What tasks are recorded for the "
                        "Project Management Application?"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "answer_required": True,
                    "minimum_citations": 1,
                    "citation_source_prefix": (
                        "student1:backend-api:"
                    ),
                    "confidence_required": True,
                },
            },
            {
                "id": "student1_rag_insufficient_context",
                "feature": FEATURE,
                "description": (
                    "Verify an unsupported question does not "
                    "produce a fabricated Project Management answer."
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
