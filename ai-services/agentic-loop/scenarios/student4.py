"""Student 4 - Skill Profile agentic validation scenarios.

This module defines feature-specific validation scenarios executed by the
single shared Release 1 agentic loop.

Student 4 owns the scenarios in this module.

Scenarios may validate:
- feature-specific MCP tools
- feature-specific RAG retrieval
- grounded RAG responses
- citations and confidence
- insufficient-context behaviour

Keep feature-specific validation logic here rather than placing it directly
inside the shared agent.py wherever practical.
"""


def get_scenarios():
    """Return this feature's MCP and RAG validation scenarios."""
    return {
        "mcp": [
            {
                "id": "student4_mcp_get_profile_1",
                "feature": "student-4-skill-profile",
                "description": "Retrieve seeded Skill Profile 1 via MCP.",
                "action": "call_tool",
                "tool": "student4_get_skill_profile",
                "arguments": {"profile_id": 1},
                "expected": {
                    "success": True,
                    "profile_id": 1,
                    "student_id": 1,
                    "skill_names_include": ["Python", "SQL"],
                },
            },
            {
                "id": "student4_mcp_missing_profile",
                "feature": "student-4-skill-profile",
                "description": "Report a nonexistent Skill Profile clearly.",
                "action": "call_tool",
                "tool": "student4_get_skill_profile",
                "arguments": {"profile_id": 99999},
                "expected": {
                    "success": False,
                    "profile_id": 99999,
                    "status_code": 404,
                    "error_required": True,
                },
            },
        ],
        "rag": [
            {
                "id": "student4_rag_retrieve_profile_1",
                "feature": "student-4-skill-profile",
                "description": "Retrieve Profile 1's Python skill and weakness.",
                "action": "retrieve",
                "request": {
                    "query": (
                        "Skill Profile ID 1 Python weakness "
                        "Advanced libraries"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "minimum_results": 1,
                    "source_ids_include": ["student-4:/api/profiles/1"],
                },
            },
            {
                "id": "student4_rag_answer_profile_1",
                "feature": "student-4-skill-profile",
                "description": "Answer with Profile 1 evidence and a citation.",
                "action": "answer",
                "request": {
                    "query": (
                        "For Skill Profile ID 1, what is the "
                        "weakness recorded for Python?"
                    ),
                    "k": 5,
                    "caller": "shared-agentic-loop",
                },
                "expected": {
                    "status": "success",
                    "answer_required": True,
                    "answer_contains": "Advanced libraries",
                    "minimum_citations": 1,
                    "citation_source_ids_include": [
                        "student-4:/api/profiles/1"
                    ],
                    "confidence_required": True,
                },
            },
            {
                "id": "student4_rag_insufficient_context",
                "feature": "student-4-skill-profile",
                "description": "Avoid inventing unsupported tuition information.",
                "action": "answer",
                "request": {
                    "query": (
                        "What is the tuition fee for Skill Profile "
                        "student ID 1?"
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