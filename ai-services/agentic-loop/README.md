# Shared Agentic Validation Loop

The repository uses one shared non-containerised agentic loop for Release 1
and Release 2 validation rather than separate runners for each student.

The shared loop follows:

`Plan -> Act -> Observe -> Adapt`

## Structure

- `agent.py` - shared command-line entry point and orchestration
- `core/runner.py` - executes Release 1 MCP/RAG scenarios and dispatches Release 2 reviews
- `core/review_runner.py` - validates Release 2 review outcomes
- `core/audit.py` - records structured validation activity and results
- `reviews/collectors.py` - collects real workflow, testing, and deployment evidence
- `reviews/llm_review.py` - performs two-stage implementation and reviewer assessment
- `scenarios/studentX.py` - feature-specific scenarios owned by each student

## Release 1 Modes

- `mcp`
- `rag`
- `all` - runs the Release 1 MCP and RAG validation modes

## Release 2 Review Modes

- `multi-agent-review`
- `testing-report-review`
- `cloud-deployment-review`
- `release2` - runs all three Release 2 review modes

Release 2 review modes collect real project evidence before using the local
LLM review stages. Missing required evidence is reported as unavailable rather
than being treated as a successful review.

The raw JSONL audit output under `evidence/` is local runtime evidence and is
not committed. Required submission/report evidence can be exported into the
repository's `reports/release2/` directory.
