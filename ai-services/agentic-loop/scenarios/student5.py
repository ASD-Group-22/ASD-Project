"""Student 5 - AI Campus Space Finder Release 1 validation scenarios."""

import os

STUDENT5_BACKEND_URL = os.getenv(
    "STUDENT5_BACKEND_URL", "http://127.0.0.1:8055"
).rstrip("/")


def get_scenarios():
    return {
        "mcp": [
            {
                "name": "Student 5 MCP campus-space filter",
                "endpoint": f"{STUDENT5_BACKEND_URL}/api/mcp",
                "json": {
                    "tool": "student5_find_campus_spaces",
                    "arguments": {
                        "min_capacity": 2,
                        "required_facilities": [],
                        "accessible_only": False,
                        "limit": 3,
                    },
                },
                "expect": "mcp_tool_result",
                "timeout": 30,
            }
        ],
        "rag": [
            {
                "name": "Student 5 grounded RAG answer",
                "endpoint": f"{STUDENT5_BACKEND_URL}/api/rag",
                "json": {"query": "What does the AI Campus Space Finder not provide?"},
                "expect": "grounded_rag",
                "timeout": 90,
            },
            {
                "name": "Student 5 insufficient-context handling",
                "endpoint": f"{STUDENT5_BACKEND_URL}/api/rag",
                "json": {"query": "What are the current helicopter parking prices on Mars?"},
                "expect": "insufficient_context",
                "timeout": 30,
            },
        ],
    }
