"""Student 4 - Skill Profile MCP tools.

Student 4 owns the feature-specific MCP tool implementations in this
module.

Tools should:
- expose useful operations for the Skill Profile feature
- access feature data through the Student 4 backend/API
- return structured responses
- follow the shared MCP tool contracts
- avoid direct access to another feature's database
"""

import os
import requests


BACKEND_URL = os.getenv(
    "STUDENT4_BACKEND_URL",
    "http://localhost:5005"
).rstrip("/")


def register_tools(mcp):
    """Register Student 4 MCP tools with the shared MCP server."""

    @mcp.tool()
    def student4_get_skill_profile(profile_id: int) -> dict:
        """Get a Skill Profile by profile ID."""
        if profile_id <= 0:
            return {
                "success": False,
                "error": "profile_id must be a positive integer",
            }

        try:
            response = requests.get(
                f"{BACKEND_URL}/api/profiles/{profile_id}",
                timeout=10,
            )
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            return {
                "success": False,
                "error": f"Skill Profile backend unavailable: {error}",
            }

        if response.status_code != 200:
            return {
                "success": False,
                "profile_id": profile_id,
                "status_code": response.status_code,
                "error": data.get("error", "Profile request failed"),
            }

        return {
            "success": True,
            "profile_id": profile_id,
            "profile": data,
        }