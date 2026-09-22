# Shared MCP Server

Release 1 uses one shared local MCP server for all five student features.

Feature-specific MCP tool implementations are separated into:

- `tools/student1.py`
- `tools/student2.py`
- `tools/student3.py`
- `tools/student4.py`
- `tools/student5.py`

The shared `server.py` is responsible for hosting and registering the tools
provided by those feature modules.

## Design Boundary

A feature-specific MCP tool should communicate with the owning feature through
its backend/API where application data is required.

MCP tools should not directly manipulate another feature's SQLite database.

## Ownership

Each student primarily maintains their own `tools/studentX.py` module.

Changes to the shared MCP server or common contracts should be coordinated with
the team because they affect all features.
