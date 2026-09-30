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
        raise RuntimeError("MCP tool returned an error")

    structured = getattr(result, "structured_content", None)

    if isinstance(structured, dict):
        return structured

    for item in getattr(result, "content", []):
        text = getattr(item, "text", None)

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
        raise RuntimeError("MCP Mode is disabled")

    return asyncio.run(
        _call_tool_async(
            tool_name,
            arguments,
        )
    )


def search_skills(
    skill: str,
    caller: str = "student-2-backend",
) -> dict:
    skill = str(skill or "").strip()

    if not skill:
        raise ValueError("skill is required")

    return call_tool(
        "student2_search_skills",
        {
            "skill": skill,
            "caller": caller,
        },
    )


def get_listing(
    listing_id: int,
    caller: str = "student-2-backend",
) -> dict:
    listing_id = int(listing_id)

    if listing_id <= 0:
        raise ValueError(
            "listing_id must be a positive integer"
        )

    return call_tool(
        "student2_get_listing",
        {
            "listing_id": listing_id,
            "caller": caller,
        },
    )