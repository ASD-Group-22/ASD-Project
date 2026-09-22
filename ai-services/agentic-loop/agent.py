"""Shared Release 1 agentic validation loop.

Provides the single team-level Plan -> Act -> Observe -> Adapt workflow.

Responsibilities:
- Support MCP validation mode.
- Support RAG validation mode.
- Support combined validation.
- Load feature-specific scenarios for all five student features.
- Produce a combined validation summary.

Feature-specific validation logic belongs in scenarios/student1.py through
scenarios/student5.py.
"""
