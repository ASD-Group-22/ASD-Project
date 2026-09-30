"""
Shared Release 1 MCP Server.

Uses MCP Python SDK 2.x.

The server exposes the MCP tools contributed by each student
feature over Streamable HTTP.

Endpoint:
    http://localhost:5100/mcp
"""

from mcp.server import MCPServer

from tools.student1 import register_tools as register_student1_tools
from tools.student2 import register_tools as register_student2_tools


# =========================================================
# MCP SERVER
# =========================================================

mcp = MCPServer(
    "University Management MCP"
)


# =========================================================
# REGISTER STUDENT TOOLS
# =========================================================

register_student1_tools(mcp)
register_student2_tools(mcp)


# =========================================================
# SERVER STARTUP
# =========================================================

if __name__ == "__main__":

    print("Starting University Management MCP Server...")
    print("Server status: RUNNING")
    print("")
    print("MCP version: 2.x")
    print("Transport: Streamable HTTP")
    print("MCP endpoint: http://localhost:5100/mcp")
    print("")
    print("Available tools:")
    print("- project_details")
    print("- project_tasks")
    print("- search_tasks")
    print("- student2_search_skills")
    print("- student2_get_listing")
    print("")

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=5100,
    )