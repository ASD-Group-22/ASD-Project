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

    # Release 2 reviews are executed by the existing shared agentic-loop
    # runner. They point to real generated evidence instead of duplicating
    # a feature-specific agentic loop.
    scenarios['multi-agent-review'] = [
        {
            'id': 'student3_multi_agent_workflow_review',
            'feature': 'student-3-group-formation',
            'review_title': 'Student 3 Multi-Agent Workflow Review',
            'description': (
                'Review a completed Student 3 group-formation workflow for '
                'Planner, Worker, Reviewer, evidence grounding and human review.'
            ),
            'review': {
                'feature': 'student3',
                'workflow_dir': 'ai-services/multi-agent-server/runtime/workflows',
            },
        },
    ]
    scenarios['testing-report-review'] = [
        {
            'id': 'student3_testing_report_review',
            'feature': 'student-3-group-formation',
            'review_title': 'Student 3 Testing Report Review',
            'description': (
                'Review Student 3 Release 2 pre-commit and post-commit endpoint '
                'testing evidence and identify unsupported claims, gaps or risks.'
            ),
            'review': {
                'primary_path': 'reports/release2/student-3-testing-report.md',
                'supplemental_paths': [
                    '.pre-commit-config.yaml',
                    '.github/workflows/student-3-ci.yml',
                    'student-3/tests/release2/test_endpoints.py',
                ],
            },
        },
    ]
    scenarios['cloud-deployment-review'] = [
        {
            'id': 'student3_cloud_deployment_review',
            'feature': 'student-3-group-formation',
            'review_title': 'Student 3 Cloud Deployment Report Review',
            'description': (
                'Review the integrated Release 2 cloud evidence, including Student 3 '
                'core group-formation availability and disabled local AI-service baseline.'
            ),
            'review': {
                'primary_path': 'reports/release2/cloud-deployment-report.md',
                'supplemental_paths': ['.github/workflows/cloud-deployment.yml'],
            },
        },
    ]
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
