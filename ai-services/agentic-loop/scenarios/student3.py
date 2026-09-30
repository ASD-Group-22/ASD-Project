"""Feature-owned scenarios for the shared runner; no separate server or runner."""
import os
import requests


def get_scenarios():
    subject = os.getenv('STUDENT3_VALIDATION_SUBJECT', 'ASD')
    scenarios = {
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

    # Match Student 2's declarative shared-runner contract. Retain path/payload/expect
    # for the Student 3 backend validation adapter until shared runner integration.
    for mode, cases in scenarios.items():
        for case in cases:
            case['feature'] = 'student-3-group-formation'
            case['description'] = case['id'].replace('_', ' ')
            if mode == 'mcp':
                case.update(action='call_tool', tool=case['payload']['tool'],
                            arguments={k: v for k, v in case['payload'].items() if k != 'tool'})
                case['arguments']['caller'] = 'shared-agentic-loop'
                case['expected'] = {'status': 'success', 'tool': case['tool']}
            else:
                case.update(action='answer', request={**case['payload'], 'caller': 'shared-agentic-loop'})
                case['expected'] = ({'status': 'insufficient_context', 'answer': 'Insufficient context.',
                                     'citation_count': 0, 'confidence_category': 'Insufficient'}
                                    if case['expect'] == 'insufficient_context' else
                                    {'status': 'success', 'answer_required': True, 'minimum_citations': 1,
                                     'citation_source_prefix': 'student-3:', 'confidence_required': True})
    scenarios['rag'].insert(0, {
        'id': 'student3_retrieve_requirements', 'feature': 'student-3-group-formation',
        'description': 'Retrieve recorded Student 3 requirements.', 'action': 'retrieve',
        'request': {'query': f'Project Group Formation {subject} skill requirements', 'k': 5, 'caller': 'shared-agentic-loop'},
        'expected': {'status': 'success', 'minimum_results': 1, 'source_prefix': 'student-3:'},
        'path': '/r1/rag/retrieve', 'payload': {'query': f'Project Group Formation {subject} skill requirements', 'k': 5},
        'expect': 'retrieval'})
    return scenarios


def validate_result(scenario, data):
    """Return diagnostic failures; citation shape does not prove semantic accuracy."""
    if not isinstance(data, dict):
        return ['Response is not an object.']
    expected = scenario['expect']
    if expected == 'insufficient_context':
        ok = (data.get('status') == 'insufficient_context' and bool(data.get('answer'))
              and data.get('confidence_category') == 'Insufficient' and data.get('citations') == [])
        return [] if ok else ['Missing explicit insufficient-context response.']
    if data.get('status') != 'success':
        return ['The service did not report success.']
    if expected == 'requirements':
        ok = (data.get('subject') == scenario['payload']['subject']
              and isinstance(data.get('requirements'), dict) and bool(data['requirements']))
        return [] if ok else ['Subject mismatch or no seeded requirements to validate.']
    if expected == 'groups':
        return [] if isinstance(data.get('groups'), list) else ['Groups must be an array.']
    if expected == 'retrieval':
        rows = data.get('results')
        return [] if isinstance(rows, list) and any(isinstance(r, dict) and str(r.get('source_id', '')).startswith('student-3:') for r in rows) else ['No Student 3 retrieval results.']
    citations = data.get('citations')
    if not isinstance(citations, list) or not citations or not data.get('answer'):
        return ['Grounded answer or citations missing.']
    if data.get('confidence_category') not in ('High', 'Medium', 'Low'):
        return ['Missing confidence category.']
    if not any(isinstance(c, dict) and str(c.get('source_id', '')).startswith('student-3:') and c.get('chunk_id') for c in citations):
        return ['No Student 3 citation. Check shared corpus integration.']
    return []


def run_scenario(scenario):
    """Shared runner calls this function for each item returned by get_scenarios()."""
    base = os.getenv('STUDENT3_BACKEND_URL', 'http://localhost:5009').rstrip('/')
    try:
        response = requests.post(base + scenario['path'], json=scenario['payload'], timeout=(5, 165))
        response.raise_for_status()
        data = response.json()
        errors = validate_result(scenario, data)
        return {'id': scenario['id'], 'passed': not errors, 'errors': errors, 'response': data}
    except (requests.RequestException, ValueError) as exc:
        return {'id': scenario['id'], 'passed': False, 'errors': [str(exc)]}
