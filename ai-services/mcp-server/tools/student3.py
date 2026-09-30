"""Read-only Student 3 tools; register on the team's existing FastMCP instance."""
import os
from urllib.parse import quote
import requests


def _get(path):
    base = os.getenv('STUDENT3_BACKEND_URL', 'http://localhost:5000').rstrip('/')
    response = requests.get(base + path, timeout=10)
    response.raise_for_status()
    return response.json()


def student3_group_requirements(subject: str) -> dict:
    """Read recorded skill requirements for a subject; performs no writes."""
    if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 100:
        return {'status': 'error', 'error': 'subject must contain 1 to 100 characters'}
    subject = subject.strip()
    try:
        data = _get('/ui/skills/' + quote(subject, safe=''))
        if not isinstance(data, dict) or 'error' in data or 'message' in data:
            raise ValueError('Unexpected requirements response')
        return {'status': 'success', 'student': 'student3', 'subject': subject,
                'requirements': data, 'source_id': 'student3:backend:/ui/skills/' + quote(subject, safe='')}
    except (requests.RequestException, ValueError):
        return {'status': 'error', 'error': 'Student 3 requirements API unavailable or invalid'}


def student3_list_groups() -> dict:
    """Read finalised groups from the owning backend; performs no writes."""
    try:
        data = _get('/ui/groups')
        if not isinstance(data, list) or any(not isinstance(g, dict) or 'group_name' not in g or 'members' not in g for g in data):
            raise ValueError('Unexpected groups response')
        return {'status': 'success', 'student': 'student3', 'groups': data,
                'source_id': 'student3:backend:/ui/groups'}
    except (requests.RequestException, ValueError):
        return {'status': 'error', 'error': 'Student 3 groups API unavailable or invalid'}


def register_tools(mcp):
    mcp.tool()(student3_group_requirements)
    mcp.tool()(student3_list_groups)
