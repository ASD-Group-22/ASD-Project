"""Shared Release 1 MCP server.

This module hosts MCP tools contributed by all five student features.

Feature-specific MCP tool implementations belong in:
- tools/student1.py
- tools/student2.py
- tools/student3.py
- tools/student4.py
- tools/student5.py

The final shared server will register those modules and expose the resulting
tools through one local MCP service.
"""

from mcp.server.fastmcp import FastMCP

from tools.student1 import (
    get_project_details,
    get_project_tasks,
    search_project_tasks,
)


mcp = FastMCP("University Management MCP")


AVAILABLE_TOOLS = [
    "project_details",
    "project_tasks",
    "search_tasks",
]


@mcp.tool()
def project_details(project_id: int):
    return get_project_details(project_id)


@mcp.tool()
def project_tasks(project_id: int):
    return get_project_tasks(project_id)


@mcp.tool()
def search_tasks(
    project_id: int,
    search_term: str
):
    return search_project_tasks(
        project_id,
        search_term
    )


if __name__ == "__main__":
    print("Starting University Management MCP Server...")
    print("Server status: RUNNING")
    print("Interact with MCP tools from a second terminal.")
    print("Available tools:")

    for tool in AVAILABLE_TOOLS:
        print(f"- {tool}")

    mcp.run()