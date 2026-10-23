"""Regression coverage for unnamed legacy groups and validated manual CRUD."""
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'student-3/backend-service'))
from app import create_app
from routes import normal_ui


@pytest.mark.parametrize('payload', [
    {'group_name': '', 'members': [1]},
    {'group_name': '   ', 'members': [1]},
    {'group_name': 'Group', 'members': []},
    {'group_name': 'Group', 'members': [True]},
    {'group_name': 'Group', 'members': [1, 1]},
    {'group_name': 'Group', 'members': ['unknown']},
    {'group_name': 'Group', 'members': [999]},
])
def test_invalid_groups_never_write(monkeypatch, payload):
    monkeypatch.setattr(normal_ui, 'load_profiles', lambda: [{'student_id': 1}])
    post = Mock(side_effect=AssertionError('Invalid create reached database'))
    put = Mock(side_effect=AssertionError('Invalid edit reached database'))
    monkeypatch.setattr(normal_ui.requests, 'post', post)
    monkeypatch.setattr(normal_ui.requests, 'put', put)
    client = create_app().test_client()
    assert client.post('/ui/groups/finalise', json=payload).status_code == 400
    assert client.put('/ui/groups/by-id/1', json=payload).status_code == 400
    post.assert_not_called()
    put.assert_not_called()


def test_edit_uses_put_and_delete_needs_no_profiles(monkeypatch):
    monkeypatch.setattr(normal_ui, 'load_profiles', lambda: [{'student_id': 1}])
    response = Mock(status_code=200)
    response.json.return_value = {'message': 'Group updated'}
    put = Mock(return_value=response)
    delete = Mock(return_value=response)
    monkeypatch.setattr(normal_ui.requests, 'put', put)
    monkeypatch.setattr(normal_ui.requests, 'delete', delete)
    client = create_app().test_client()
    assert client.put('/ui/groups/by-id/7', json={'group_name': ' Repaired ', 'members': ['1']}).status_code == 200
    assert put.call_args.kwargs['json'] == {'group_name': 'Repaired', 'members': [1]}
    delete.assert_not_called()
    monkeypatch.setattr(normal_ui, 'load_profiles', Mock(side_effect=AssertionError('Delete must not load profiles')))
    assert client.delete('/ui/groups/by-id/7').status_code == 200
    assert delete.call_args.args[0].endswith('/groups/by-id/7')


def test_database_legacy_recovery_and_atomic_update(tmp_path):
    # A separate process avoids backend/database app and services module collisions.
    env = os.environ.copy()
    env['DATABASE_URL'] = 'sqlite:///' + str(tmp_path / 'groups.db')
    code = """
from app import app, SessionLocal, Group
client = app.test_client()
with SessionLocal() as db:
    broken = Group(name='', members=['not a student'])
    other = Group(name='', members=[999])
    db.add_all([broken, other]); db.commit()
    broken_id, other_id = broken.id, other.id
assert len(client.get('/groups').json) == 2
assert client.post('/groups', json={'group_name': '', 'members': [1]}).status_code == 400
assert client.put(f'/groups/by-id/{broken_id}', json={'group_name': 'Fixed', 'members': []}).status_code == 400
assert client.get('/groups').json[0]['group_name'] == ''
assert client.put(f'/groups/by-id/{broken_id}', json={'group_name': "Fixed / O'Neil", 'members': [1]}).status_code == 200
rows = client.get('/groups').json
assert rows[0]['id'] == broken_id and rows[0]['group_name'] == "Fixed / O'Neil"
assert rows[1]['id'] == other_id and rows[1]['group_name'] == ''
assert client.delete(f'/groups/by-id/{other_id}').status_code == 200
assert client.delete(f'/groups/by-id/{other_id}').status_code == 404
assert len(client.get('/groups').json) == 1
assert client.delete(f'/groups/by-id/{broken_id}').status_code == 200
assert client.get('/groups').json == []
"""
    env['PYTHONPATH'] = str(ROOT / 'student-3/database-service')
    result = subprocess.run([sys.executable, '-B', '-c', code], cwd=tmp_path, env=env, capture_output=True, text=True)  # noqa: S603 - fixed interpreter and internal test input
    assert result.returncode == 0, result.stdout + result.stderr
