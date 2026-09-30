"""Feature-owned scenarios for the shared runner; no separate server or runner."""
import os
import requests


def get_scenarios():
    subject = os.getenv('STUDENT3_VALIDATION_SUBJECT', 'ASD')
    return {
        'mcp': [
            {'id': 'student3_requirements', 'path': '/r1/mcp',
             'payload': {'tool': 'student3_group_requirements', 'subject': subject},
             'expect': 'requirements'},
            {'id': 'student3_groups', 'path': '/r1/mcp',
             'payload': {'tool': 'student3_list_groups'}, 'expect': 'groups'},
        ],
        'rag': [
            {'id': 'student3_grounded_requirements', 'path': '/r1/rag',
             'payload': {'query': f'What skill requirements are recorded for subject {subject} in Project Group Formation?', 'k': 5},
             'expect': 'grounded'},
            {'id': 'student3_insufficient_context', 'path': '/r1/rag',
             'payload': {'query': 'What is the exact final exam mark of student 999999 in year 2099?', 'k': 5},
             'expect': 'insufficient_context'},
        ],
    }


def validate_result(scenario, data):
    """Return diagnostic failures; citation shape does not prove semantic accuracy."""
    if not isinstance(data, dict):
        return ['Response is not an object.']
    expected = scenario['expect']
    if expected == 'insufficient_context':
        ok = (data.get('status') == 'insufficient_context' and bool(data.get('answer'))
              and data.get('confidence_category') == 'Unknown' and data.get('citations') == [])
        return [] if ok else ['Missing explicit insufficient-context response.']
    if data.get('status') != 'success':
        return ['The service did not report success.']
    if expected == 'requirements':
        ok = (data.get('subject') == scenario['payload']['subject']
              and isinstance(data.get('requirements'), dict) and bool(data['requirements']))
        return [] if ok else ['Subject mismatch or no seeded requirements to validate.']
    if expected == 'groups':
        return [] if isinstance(data.get('groups'), list) else ['Groups must be an array.']
    citations = data.get('citations')
    if not isinstance(citations, list) or not citations or not data.get('answer'):
        return ['Grounded answer or citations missing.']
    if data.get('confidence_category') not in ('High', 'Medium', 'Low'):
        return ['Missing confidence category.']
    if not any(isinstance(c, dict) and str(c.get('source_id', '')).startswith('student3:') and c.get('chunk_id') for c in citations):
        return ['No Student 3 citation. Check shared corpus integration.']
    return []


def run_scenario(scenario):
    """Shared runner calls this function for each item returned by get_scenarios()."""
    base = os.getenv('STUDENT3_BACKEND_URL', 'http://localhost:5000').rstrip('/')
    try:
        response = requests.post(base + scenario['path'], json=scenario['payload'], timeout=(5, 165))
        response.raise_for_status()
        data = response.json()
        errors = validate_result(scenario, data)
        return {'id': scenario['id'], 'passed': not errors, 'errors': errors, 'response': data}
    except (requests.RequestException, ValueError) as exc:
        return {'id': scenario['id'], 'passed': False, 'errors': [str(exc)]}
