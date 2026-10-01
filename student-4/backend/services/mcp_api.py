import asyncio
import json
import os

from mcp import Client


MCP_URL = os.getenv(
    "MCP_URL", "http://host.docker.internal:5100/mcp"
).rstrip("/")


async def _get_profile(profile_id: int) -> dict:
    async with Client(MCP_URL) as client:
        result = await client.call_tool(
            "student4_get_skill_profile",
            {"profile_id": profile_id},
        )

    if getattr(result, "is_error", False):
        raise RuntimeError("MCP tool returned an error")

    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured

    for item in getattr(result, "content", []):
        value = getattr(item, "text", None)
        if value:
            try:
                payload = json.loads(value)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                pass

    raise ValueError("MCP tool returned no JSON object")


def get_profile_via_mcp(profile_id: int) -> dict:
    if os.getenv("MCP_ENABLED", "true").lower() in ("false", "0", "no"):
        raise RuntimeError("MCP Mode is disabled")

    return asyncio.run(_get_profile(profile_id))