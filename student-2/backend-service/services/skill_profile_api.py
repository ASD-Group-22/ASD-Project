import os
import requests

SKILL_PROFILE_SERVICE_URL = os.getenv("SKILL_PROFILE_SERVICE_URL", "").strip().rstrip("/")


def get_profile(student_id):
    """Optional Student 4 integration. Never reads another service's SQLite file directly."""
    if not SKILL_PROFILE_SERVICE_URL:
        return None
    try:
        response = requests.get(
            f"{SKILL_PROFILE_SERVICE_URL}/api/profiles/{student_id}", timeout=3
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        body = response.json()
        return body if isinstance(body, dict) else {"profile": body}
    except (requests.RequestException, ValueError):
# profile enrichment is optional so the core Skill Exchange service
# can continue if the skill profile service is unavailable.
        return None
