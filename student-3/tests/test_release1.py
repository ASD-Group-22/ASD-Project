"""Offline R1 contract tests. No Ollama, MCP or RAG server is required."""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'student-3/backend-service'))
from routes import release1 as routes
from services import release1_client as clients


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tools = load('s3_r1_tools', 'ai-services/mcp-server/tools/student3.py')
sources = load('s3_r1_sources', 'ai-services/rag-server/sources/student3.py')
scenarios = load('s3_r1_scenarios', 'ai-services/agentic-loop/scenarios/student3.py')


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('MCP_ENABLED', 'true')
    monkeypatch.setenv('RAG_ENABLED', 'true')
    app = Flask(__name__)
    app.register_blueprint(routes.r1_bp, url_prefix='/r1')
    return app.test_client()


@pytest.mark.parametrize('mode', ['mcp', 'rag'])
def test_disabled_modes_never_call_services(client, monkeypatch, mode):
    monkeypatch.setenv(mode.upper() + '_ENABLED', 'false')
    call = Mock(side_effect=AssertionError('Must not contact external services'))
    monkeypatch.setattr(routes, 'call_' + mode, call)
    assert client.post('/r1/' + mode, json={}).status_code == 503
    call.assert_not_called()


def test_tool_allowlist_and_arguments(client, monkeypatch):
    call = Mock(return_value={'status': 'success', 'requirements': {}})
    monkeypatch.setattr(routes, 'call_mcp', call)
    assert client.post('/r1/mcp', json={'tool': 'delete_all'}).status_code == 400
    assert client.post('/r1/mcp', json={'tool': 'student3_group_requirements', 'subject': ''}).status_code == 400
    call.assert_not_called()
    assert client.post('/r1/mcp', json={'tool': 'student3_group_requirements', 'subject': ' ASD ', 'url': 'ignored'}).status_code == 200
    call.assert_called_once_with('student3_group_requirements', {'subject': 'ASD'})


def test_mcp_error_is_visible(client, monkeypatch):
    monkeypatch.setattr(routes, 'call_mcp', Mock(side_effect=clients.ServiceError('Unavailable')))
    response = client.post('/r1/mcp', json={'tool':'student3_list_groups'})
    assert response.status_code == 503 and response.json['error'] == 'Unavailable'


@pytest.mark.parametrize('payload', [[], {}, {'query':'x','k':True}, {'query':'x','k':11}, {'query':'x'*1001}])
def test_bad_rag_input_does_not_call_service(client, monkeypatch, payload):
    call = Mock()
    monkeypatch.setattr(routes, 'call_rag', call)
    assert client.post('/r1/rag', json=payload).status_code == 400
    call.assert_not_called()


def grounded():
    return {'status':'success','answer':'Python is required.', 'confidence_category':'Medium',
            'citations':[{'source_id':'student3:backend:/ui/skills/ASD','chunk_id':'student3_requirements_abc'}]}


def test_citations_and_confidence_preserved(client, monkeypatch):
    monkeypatch.setattr(routes, 'call_rag', lambda q,k: clients.validate_rag(grounded()))
    assert client.post('/r1/rag', json={'query':'ASD requirements'}).json == grounded()


def test_no_citations_means_insufficient_context():
    data=grounded(); data['citations']=[]
    result=clients.validate_rag(data)
    assert result['status']=='insufficient_context'
    assert result['confidence_category']=='Unknown'
    assert result['answer'] != data['answer']


def test_model_outage_is_not_grounded_answer():
    data=grounded(); data['answer']='Ollama unavailable: connection failed'
    with pytest.raises(clients.ServiceError): clients.validate_rag(data)


def test_bad_citation_rejected():
    data=grounded(); data['citations']=[{'source_id':'student3:x'}]
    with pytest.raises(clients.ServiceError): clients.validate_rag(data)


def test_tool_registration_on_existing_instance():
    class Registry:
        def __init__(self): self.names=[]
        def tool(self):
            def register(fn): self.names.append(fn.__name__); return fn
            return register
    server=Registry(); tools.register_tools(server)
    assert server.names==['student3_group_requirements','student3_list_groups']


def test_tool_encodes_subject_and_uses_own_api(monkeypatch):
    get=Mock(return_value={'python': {'level':'advanced'}})
    monkeypatch.setattr(tools,'_get',get)
    result=tools.student3_group_requirements('A/B')
    get.assert_called_once_with('/ui/skills/A%2FB')
    assert result['status']=='success'


def test_source_both_interfaces_and_stable_ids(monkeypatch):
    records={'/ui/subjects':['ASD'], '/ui/groups':[{'group_name':'G1','members':['Student 1']}],
             '/ui/skills/ASD':{'python':{'level':'advanced','amount':'moderate'}}}
    monkeypatch.setattr(sources,'_get',lambda p: records[p])
    docs=sources.get_documents()
    chunks=sources.build_chunks()['chunks']
    assert [d['chunk_id'] for d in docs]==[d['chunk_id'] for d in chunks]
    assert len(docs)==2
    assert all(d['metadata']['student']=='student3' and d['source_id'].startswith('student3:backend:') for d in docs)
    assert all({'chunk_id','source_id','authority_tier','text','metadata','indexed_at'} <= d.keys() for d in docs)


def test_source_failure_not_silent_partial_success(monkeypatch):
    monkeypatch.setattr(sources,'_get',Mock(side_effect=ValueError('bad response')))
    assert sources.build_chunks()['status']=='error'
    with pytest.raises(ValueError): sources.get_documents()


def test_scenarios_detect_wrong_feature_citations():
    scenario=scenarios.get_scenarios()['rag'][0]
    assert scenarios.validate_result(scenario,grounded())==[]
    data=grounded(); data['citations'][0]['source_id']='student1:project:1'
    assert scenarios.validate_result(scenario,data)


def test_scenarios_require_real_insufficient_outcome():
    scenario=scenarios.get_scenarios()['rag'][1]
    assert scenarios.validate_result(scenario,grounded())
    assert not scenarios.validate_result(scenario,{'status':'insufficient_context', 'answer':'Insufficient context.',
                                                  'confidence_category':'Unknown','citations':[]})
