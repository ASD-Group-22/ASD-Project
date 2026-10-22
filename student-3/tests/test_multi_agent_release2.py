from pathlib import Path
import importlib.util
import sys
from unittest.mock import Mock

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'student-3/backend-service'))
from app import create_app
from routes import multi_agent_mode


def _load_adapter():
    path = ROOT / 'ai-services/multi-agent-server/adapters/student3.py'
    spec = importlib.util.spec_from_file_location('student3_multi_agent_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(multi_agent_mode.multi_agent_api, 'is_enabled', lambda: True)
    return create_app().test_client()


def test_create_workflow_forwards_validated_group_context(client, monkeypatch):
    create = Mock(return_value={'workflow_id': 'workflow-1', 'status': 'awaiting_human_review'})
    monkeypatch.setattr(multi_agent_mode.multi_agent_api, 'create_group_workflow', create)
    response = client.post('/r2/multi-agent/workflows', json={
        'subject': ' ASD ', 'group_size': 5, 'student_ids': [1, 2, 3], 'user_request': 'Balance groups.'
    })
    assert response.status_code == 201
    assert create.call_args.args == ('ASD', 5, [1, 2, 3], 'Balance groups.')


@pytest.mark.parametrize('payload', [
    {}, {'subject': '', 'student_ids': [1, 2, 3]},
    {'subject': 'ASD', 'group_size': 2, 'student_ids': [1, 2, 3]},
    {'subject': 'ASD', 'student_ids': [1, 1, 2]},
    {'subject': 'ASD', 'student_ids': ['1', 2, 3]},
])
def test_invalid_workflow_input_does_not_call_shared_service(client, monkeypatch, payload):
    create = Mock(side_effect=AssertionError('Shared service must not be called'))
    monkeypatch.setattr(multi_agent_mode.multi_agent_api, 'create_group_workflow', create)
    assert client.post('/r2/multi-agent/workflows', json=payload).status_code == 400
    create.assert_not_called()


def test_disabled_mode_blocks_requests(client, monkeypatch):
    monkeypatch.setattr(multi_agent_mode.multi_agent_api, 'is_enabled', lambda: False)
    response = client.post('/r2/multi-agent/workflows', json={'subject': 'ASD', 'student_ids': [1, 2, 3]})
    assert response.status_code == 403
    assert response.json['status'] == 'disabled'


def test_student3_adapter_uses_only_feature_api(monkeypatch):
    adapter = _load_adapter()
    calls = []
    responses = {
        '/ui/skills/ASD': {'python': {'level': 'intermediate', 'amount': 'extensive'}},
        '/ai/profiles': [
            {'student_id': 1, 'skills': []}, {'student_id': 2, 'skills': []}, {'student_id': 3, 'skills': []}
        ],
    }
    monkeypatch.setattr(adapter, '_get_json', lambda path: calls.append(path) or responses[path])
    evidence = adapter.gather_evidence('group_formation_recommendation', {'subject': 'ASD', 'group_size': 5, 'student_ids': [1, 2, 3]})
    assert calls == ['/ui/skills/ASD', '/ai/profiles']
    assert evidence['allowed_output_references'] == ['requirements:ASD', 'profile:1', 'profile:2', 'profile:3']
    assert evidence['source']['service'] == 'student-3-backend-api'
