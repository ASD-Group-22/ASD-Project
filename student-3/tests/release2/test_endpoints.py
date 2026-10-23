"""Post-commit Release 2 endpoint checks for Student 3.

These tests run against the containerised Student 3 backend after it is ready.
They do not require Ollama, MCP, RAG or the Multi-Agent service.
"""
import os

import requests


BASE_URL = os.getenv("STUDENT3_BACKEND_URL", "http://localhost:5009").rstrip("/")


def test_subjects_endpoint_returns_seeded_subjects():
    """Endpoint 1: retrieve the feature's available subjects."""
    response = requests.get(f"{BASE_URL}/ui/subjects", timeout=10)

    assert response.status_code == 200
    subjects = response.json()
    assert isinstance(subjects, list)
    assert "ASD" in subjects


def test_subject_requirements_endpoint_returns_recorded_skills():
    """Endpoint 2: retrieve the recorded requirements for the ASD subject."""
    response = requests.get(f"{BASE_URL}/ui/skills/ASD", timeout=10)

    assert response.status_code == 200
    requirements = response.json()
    assert isinstance(requirements, dict)
    assert requirements, "Expected seeded ASD skill requirements."
    assert all(isinstance(skill, str) and skill.strip() for skill in requirements)
