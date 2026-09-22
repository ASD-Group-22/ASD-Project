# Release 1 Shared AI Services

This directory contains the shared Release 1 AI infrastructure used by all five student features.

The team maintains:

- One shared MCP server
- One shared RAG server
- One shared agentic validation loop

Each student owns the feature-specific modules associated with their assigned service.

## Ownership

| Student | Feature | MCP | RAG | Agentic Validation |
|---|---|---|---|---|
| Student 1 | Project Management | `mcp-server/tools/student1.py` | `rag-server/sources/student1.py` | `agentic-loop/scenarios/student1.py` |
| Student 2 | Skill Exchange | `mcp-server/tools/student2.py` | `rag-server/sources/student2.py` | `agentic-loop/scenarios/student2.py` |
| Student 3 | Project Group Formation | `mcp-server/tools/student3.py` | `rag-server/sources/student3.py` | `agentic-loop/scenarios/student3.py` |
| Student 4 | Skill Profile | `mcp-server/tools/student4.py` | `rag-server/sources/student4.py` | `agentic-loop/scenarios/student4.py` |
| Student 5 | AI Campus Space Finder | `mcp-server/tools/student5.py` | `rag-server/sources/student5.py` | `agentic-loop/scenarios/student5.py` |

Shared infrastructure files such as `server.py`, `rag_pipeline.py`, `agent.py`,
`runner.py`, and `audit.py` are used by all students and should be modified carefully.

Student-specific modules should access feature data through the owning feature's
backend/API rather than directly accessing another student's database.

## Development Workflow

Release 1 feature work should branch from `release1-integration`.

Each student should primarily modify:

- their own feature directory under `student-x/`
- `mcp-server/tools/studentX.py`
- `rag-server/sources/studentX.py`
- `agentic-loop/scenarios/studentX.py`

Changes to shared infrastructure files should be coordinated with the team to
reduce merge conflicts.

Student feature branches should be merged back into `release1-integration`
through pull requests after validation.

The completed and validated Release 1 integration branch can then be reviewed
before being merged into `main`.
