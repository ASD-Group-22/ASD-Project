"""Student 2 - Skill Exchange MCP tools.

Student 2 owns the feature-specific MCP tools in this module.

Boundary:
- Reads Skill Exchange data through the Student 2 backend API.
- Does not access the SQLite database directly.
- Does not modify listings.
- Does not perform AI matching.
"""

import os

import requests


STUDENT2_BACKEND_URL = os.getenv(
    "STUDENT2_BACKEND_URL",
    "http://localhost:5202",
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv(
        "STUDENT2_MCP_TIMEOUT_SECONDS",
        "5",
    )
)


def _search_skills(
    skill: str,
    caller: str = "student-2",
) -> dict:
    """Search active Skill Exchange listings through the Student 2 API."""

    skill = str(
        skill or ""
    ).strip()

    if not skill:
        return {
            "status": "error",
            "tool": "student2_search_skills",
            "caller": caller,
            "error": "skill is required",
        }

    try:
        response = requests.get(
            f"{STUDENT2_BACKEND_URL}/skill-exchange/search",
            params={
                "skill": skill,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

        payload = response.json()
        listings = payload.get(
            "listings",
            [],
        )

        return {
            "status": "success",
            "tool": "student2_search_skills",
            "caller": caller,
            "skill": skill,
            "result_count": len(listings),
            "listings": listings,
        }

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        return {
            "status": "error",
            "tool": "student2_search_skills",
            "caller": caller,
            "skill": skill,
            "error": str(exc),
        }


def _get_listing(
    listing_id: int,
    caller: str = "student-2",
) -> dict:
    """Retrieve one Skill Exchange listing through the Student 2 API."""

    try:
        parsed_listing_id = int(
            listing_id
        )

        if parsed_listing_id <= 0:
            raise ValueError(
                "listing_id must be a positive integer"
            )

    except (
        TypeError,
        ValueError,
    ) as exc:
        return {
            "status": "error",
            "tool": "student2_get_listing",
            "caller": caller,
            "error": str(exc),
        }

    try:
        response = requests.get(
            (
                f"{STUDENT2_BACKEND_URL}"
                f"/skill-exchange/{parsed_listing_id}"
            ),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 404:
            return {
                "status": "error",
                "tool": "student2_get_listing",
                "caller": caller,
                "listing_id": parsed_listing_id,
                "error": "Listing not found",
            }

        response.raise_for_status()
        listing = response.json()

        return {
            "status": "success",
            "tool": "student2_get_listing",
            "caller": caller,
            "listing": listing,
        }

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        return {
            "status": "error",
            "tool": "student2_get_listing",
            "caller": caller,
            "listing_id": parsed_listing_id,
            "error": str(exc),
        }


def register_tools(mcp):
    """Register Student 2 tools with the shared MCP server."""

    @mcp.tool()
    def student2_search_skills(
        skill: str,
        caller: str = "student-2",
    ) -> dict:
        """Search active Student 2 Skill Exchange listings by skill."""

        return _search_skills(
            skill=skill,
            caller=caller,
        )

    @mcp.tool()
    def student2_get_listing(
        listing_id: int,
        caller: str = "student-2",
    ) -> dict:
        """Retrieve one Student 2 Skill Exchange listing by listing ID."""

        return _get_listing(
            listing_id=listing_id,
            caller=caller,
        )

    return None
