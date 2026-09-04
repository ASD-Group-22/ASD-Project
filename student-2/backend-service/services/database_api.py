import os
import requests

DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL", "http://student-2-skill-exchange-database:5002"
).rstrip("/")


def _request(method, path, **kwargs):
    return requests.request(method, f"{DATABASE_SERVICE_URL}{path}", timeout=5, **kwargs)


def get_listings(include_inactive=False):
    response = _request("GET", "/listings", params={"include_inactive": str(include_inactive).lower()})
    response.raise_for_status()

    return response.json()


def get_listing_response(listing_id):
    return _request("GET", f"/listings/{listing_id}")


def create_listing_response(payload):
    return _request("POST", "/listings", json=payload)


def update_listing_response(listing_id, payload):
    return _request("PUT", f"/listings/{listing_id}", json=payload)


def deactivate_listing_response(listing_id):
    return _request("DELETE", f"/listings/{listing_id}")


def search_listings(skill):
    response = _request("GET", "/listings/search", params={"skill": skill})
    response.raise_for_status()
    
    return response.json()
