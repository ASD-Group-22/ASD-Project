# Shared Agentic Validation Loop

Release 1 uses one shared team agentic loop rather than one independent loop per
student.

The shared loop follows:

`Plan -> Act -> Observe -> Adapt`

## Structure

- `agent.py` - shared entry point and orchestration
- `core/runner.py` - executes MCP/RAG validation scenarios
- `core/audit.py` - records validation activity and results
- `scenarios/studentX.py` - feature-specific scenarios owned by each student

The shared loop should support:

- MCP validation mode
- RAG validation mode
- combined validation mode

Student-specific feature logic should remain inside the corresponding scenario
module wherever practical.
