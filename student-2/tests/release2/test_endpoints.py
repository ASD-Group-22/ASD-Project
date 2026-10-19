# ruff: noqa: S101
import os

import requests


BASE_URL = os.getenv("STUDENT2_BACKEND_URL", "http://localhost:5202")


def test_search_skill_endpoint():
    """Release 2 endpoint test 1: search Skill Exchange listings."""
    response = requests.get(
        f"{BASE_URL}/skill-exchange/search",
        params={"skill": "Python"},
        timeout=10,
    )

    assert response.status_code == 200

    payload = response.json()
    listings = payload.get("listings")

    assert isinstance(listings, list)
    assert listings, "Expected at least one seeded Python-related listing."

    searchable_text = [
        f"{item.get('skill_offered', '')} {item.get('skill_wanted', '')}".lower()
        for item in listings
    ]

    assert any("python" in text for text in searchable_text)


def test_deterministic_matches_endpoint():
    """Release 2 endpoint test 2: deterministic candidate matching."""
    response = requests.get(
        f"{BASE_URL}/skill-exchange/1/matches",
        timeout=10,
    )

    assert response.status_code == 200

    payload = response.json()
    listing = payload.get("listing")
    candidates = payload.get("candidates")

    assert isinstance(listing, dict)
    assert listing.get("listing_id") == 1
    assert listing.get("status") == "active"

    assert isinstance(candidates, list)
    assert candidates, "Seeded listing 1 should have at least one valid candidate."

    wanted_skill = str(listing.get("skill_wanted", "")).strip().lower()

    for candidate in candidates:
        assert candidate.get("listing_id") != listing["listing_id"]
        assert candidate.get("status") == "active"
        assert str(candidate.get("skill_offered", "")).strip().lower() == wanted_skill
        assert isinstance(candidate.get("score"), int)
        assert candidate.get("match_level") in {"Strong Match", "Partial Match"}