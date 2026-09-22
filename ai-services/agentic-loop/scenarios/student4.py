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
        "mcp": [],
        "rag": [],
    }
