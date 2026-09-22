# MCP Tool Contracts

All Release 1 MCP tools are hosted by the single shared MCP server.

## Naming

Feature-specific tools should use a student/feature namespace where practical
to prevent naming collisions.

Example:

`student2_search_skills`

## Tool Responsibilities

Each MCP tool should:

1. Perform one clearly defined operation.
2. Validate required arguments.
3. Access application data through the owning feature's backend/API.
4. Return structured results.
5. Avoid direct access to another feature's database.
6. Fail clearly when the requested operation cannot be completed.

## Registration

Each `tools/studentX.py` module exposes a `register_tools(mcp)` function.

The shared MCP server can call these registration functions to add each
student's tools to the same server.

## Ownership

Students should primarily modify their own feature-specific tool module.
Changes to this shared contract should be discussed with the team.
