"""Student 2 - Skill Exchange trusted RAG source.

This adapter retrieves Skill Exchange information through the
Student 2 backend API. It does not access SQLite directly.

The shared RAG pipeline calls get_documents() to obtain trusted
Student 2 documents for indexing and grounded retrieval.
"""

import os

import requests


STUDENT2_BACKEND_URL = os.getenv(
    "STUDENT2_BACKEND_URL",
    "http://localhost:5202",
).rstrip("/")

REQUEST_TIMEOUT_SECONDS = float(
    os.getenv(
        "STUDENT2_RAG_TIMEOUT_SECONDS",
        "15",
    )
)


def _clean(value) -> str:
    """Return a safe plain-text representation of an API field."""

    if value is None:
        return ""

    return str(value).strip()


def _fetch_listings() -> list[dict]:
    """Retrieve active Skill Exchange listings through Student 2's API."""

    response = requests.get(
        f"{STUDENT2_BACKEND_URL}/skill-exchange",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    response.raise_for_status()

    payload = response.json()

    listings = payload.get(
        "listings",
        [],
    )

    if not isinstance(
        listings,
        list,
    ):
        raise ValueError(
            "Student 2 backend returned an invalid listings payload"
        )

    return listings


def _build_documents(
    listings: list[dict],
) -> list[dict]:
    """Convert Skill Exchange listings into trusted RAG documents."""

    documents = []

    active_listings = [
        listing
        for listing in listings
        if listing.get("status") == "active"
    ]

    # One catalogue-level document provides broader Skill Exchange context.
    if active_listings:
        catalogue_entries = []

        for listing in active_listings:
            catalogue_entries.append(
                (
                    f"{_clean(listing.get('student_name'))} "
                    f"offers {_clean(listing.get('skill_offered'))} "
                    f"and wants {_clean(listing.get('skill_wanted'))}"
                )
            )

        documents.append({
            "chunk_id": "student2_skill_exchange_catalog",
            "source_id": "student-2:/skill-exchange",
            "feature": "student-2-skill-exchange",
            "authority_tier": "tier_1",
            "record_type": "catalog",
            "listing_id": -1,
            "student_name": "",
            "skill_offered": "",
            "skill_wanted": "",
            "status": "active",
            "text": (
                "Active Skill Exchange catalogue: "
                + "; ".join(catalogue_entries)
                + "."
            ),
        })

    # Each active listing also becomes an authoritative individual document.
    for listing in active_listings:
        listing_id = listing.get(
            "listing_id"
        )

        try:
            listing_id = int(
                listing_id
            )

        except (
            TypeError,
            ValueError,
        ):
            # A record without a usable identifier cannot provide a
            # stable citation, so it is not suitable for RAG ingestion.
            continue

        student_id = _clean(
            listing.get("student_id")
        )

        student_name = _clean(
            listing.get("student_name")
        )

        skill_offered = _clean(
            listing.get("skill_offered")
        )

        skill_wanted = _clean(
            listing.get("skill_wanted")
        )

        availability = _clean(
            listing.get("availability")
        )

        description = _clean(
            listing.get("description")
        )

        status = _clean(
            listing.get("status")
        )

        documents.append({
            "chunk_id": f"student2_listing_{listing_id}",
            "source_id": (
                f"student-2:/skill-exchange/{listing_id}"
            ),
            "feature": "student-2-skill-exchange",
            "authority_tier": "tier_1",
            "record_type": "listing",
            "listing_id": listing_id,
            "student_id": student_id,
            "student_name": student_name,
            "skill_offered": skill_offered,
            "skill_wanted": skill_wanted,
            "availability": availability,
            "description": description,
            "status": status,
            "text": (
                "Skill Exchange listing. "
                f"Listing ID: {listing_id}. "
                f"Student: {student_name}. "
                f"Student ID: {student_id}. "
                f"Offers: {skill_offered}. "
                f"Wants: {skill_wanted}. "
                f"Availability: {availability}. "
                f"Status: {status}. "
                f"Description: {description}"
            ),
        })

    return documents


def get_documents() -> list[dict]:
    """Return trusted Student 2 documents for shared RAG ingestion."""

    listings = _fetch_listings()

    return _build_documents(
        listings
    )

