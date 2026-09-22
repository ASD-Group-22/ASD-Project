"""Shared agentic-loop audit helper.

Responsible for recording validation actions and results for traceability.

Audit records may include:
- timestamp
- student/feature
- validation mode
- action or query
- observed result
- PASS/FAIL outcome

This is shared infrastructure and is not a separate agent.
"""
