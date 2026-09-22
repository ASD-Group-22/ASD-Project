"""Shared scenario runner.

Executes feature-specific MCP and RAG validation scenarios and evaluates their
results.

Responsibilities:
- Execute scenarios supplied by the student scenario modules.
- Collect observations from MCP and RAG services.
- Evaluate expected versus actual results.
- Return structured PASS/FAIL results to the shared agentic loop.

This is shared infrastructure and is not a separate agent.
"""
