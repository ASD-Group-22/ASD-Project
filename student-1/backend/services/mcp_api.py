import asyncio
import json
import os

from mcp import Client


MCP_ENABLED = os.getenv(
    "MCP_ENABLED",
    "true",
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


MCP_URL = os.getenv(
    "MCP_URL",
    "http://host.docker.internal:5100/mcp",
).rstrip("/")


def mcp_is_enabled() -> bool:
    return MCP_ENABLED


def _decode_tool_result(result) -> dict:

    if getattr(result, "is_error", False):
        raise RuntimeError(
            "MCP tool returned an error"
        )

    structured = getattr(
        result,
        "structured_content",
        None,
    )

    if isinstance(structured, dict):
        return structured

    for item in getattr(
        result,
        "content",
        [],
    ):

        text = getattr(
            item,
            "text",
            None,
        )

        if not text:
            continue

        try:

            payload = json.loads(text)

            if isinstance(payload, dict):
                return payload

        except json.JSONDecodeError:
            continue

    raise ValueError(
        "MCP response did not contain a valid JSON object"
    )


async def _call_tool_async(
    tool_name: str,
    arguments: dict,
) -> dict:

    async with Client(MCP_URL) as client:

        result = await client.call_tool(
            tool_name,
            arguments,
        )

        return _decode_tool_result(result)


def call_tool(
    tool_name: str,
    arguments: dict,
) -> dict:

    if not MCP_ENABLED:
        raise RuntimeError(
            "MCP Mode is disabled"
        )

    return asyncio.run(
        _call_tool_async(
            tool_name,
            arguments,
        )
    )


# =========================================================
# STUDENT 1 MCP TOOLS
# =========================================================

def get_project(
    project_id: int,
    caller: str = "student-1-backend",
) -> dict:

    project_id = int(project_id)

    if project_id <= 0:
        raise ValueError(
            "project_id must be a positive integer"
        )

    return call_tool(
        "project_details",
        {
            "project_id": project_id,
            "caller": caller,
        },
    )


def get_project_tasks(
    project_id: int,
    caller: str = "student-1-backend",
) -> dict:

    project_id = int(project_id)

    if project_id <= 0:
        raise ValueError(
            "project_id must be a positive integer"
        )

    return call_tool(
        "project_tasks",
        {
            "project_id": project_id,
            "caller": caller,
        },
    )


def search_project_tasks(
    project_id: int,
    search_term: str,
    caller: str = "student-1-backend",
) -> dict:

    project_id = int(project_id)

    if project_id <= 0:
        raise ValueError(
            "project_id must be a positive integer"
        )

    search_term = str(
        search_term or ""
    ).strip()

    if not search_term:
        raise ValueError(
            "search_term is required"
        )

    return call_tool(
        "search_tasks",
        {
            "project_id": project_id,
            "search_term": search_term,
            "caller": caller,
        },
    )