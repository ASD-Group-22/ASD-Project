"""Student 1-compatible chunks, obtained through Student 3's backend API."""
from datetime import datetime, timezone
import hashlib
import json
import os
from urllib.parse import quote
import requests


def _get(path):
    base = os.getenv('STUDENT3_BACKEND_URL', 'http://localhost:5009').rstrip('/')
    response = requests.get(base + path, timeout=10)
    response.raise_for_status()
    return response.json()


def _chunk(kind, key, path, text):
    suffix = hashlib.sha256(key.encode('utf-8')).hexdigest()[:20]
    return {'chunk_id': f'student3_{kind}_{suffix}',
            'source_id': 'student-3:' + path,
            'feature': 'student-3-group-formation', 'record_type': kind,
            'subject': key if kind == 'requirements' else '',
            'group_name': key if kind == 'group' else '',
            'authority_tier': 'tier_1', 'text': text,
            'metadata': {'source_type': 'backend_api', 'student': 'student3',
                         'record_type': kind, 'record_key': key},
            'indexed_at': datetime.now(timezone.utc).isoformat()}


def get_documents():
    """Contract interface. Raise on source failure rather than silently indexing partial data."""
    subjects = _get('/ui/subjects')
    groups = _get('/ui/groups')
    if not isinstance(subjects, list) or not all(isinstance(s, str) for s in subjects):
        raise ValueError('Invalid subjects response')
    if not isinstance(groups, list):
        raise ValueError('Invalid groups response')
    docs = []
    for subject in sorted(set(subjects)):
        path = '/ui/skills/' + quote(subject, safe='')
        requirements = _get(path)
        if not isinstance(requirements, dict) or 'error' in requirements or 'message' in requirements:
            raise ValueError('Invalid requirements response')
        if requirements:
            docs.append(_chunk('requirements', subject, path,
                f'Project Group Formation requirements for subject {subject}: ' + json.dumps(requirements, sort_keys=True)))
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get('group_name'), str) or not isinstance(group.get('members'), list):
            raise ValueError('Invalid group record')
        name = group['group_name']
        docs.append(_chunk('group', name, '/ui/groups#' + quote(name, safe=''),
            f'Project Group Formation finalised group {name}. Recorded members: ' + json.dumps(group['members'])))
    # Deliberately exclude model-generated recommendations from authoritative source facts.
    return docs


def build_chunks():
    """Student 1's current pipeline interface, alongside the scaffold interface."""
    try:
        return {'status': 'success', 'student': 'student3', 'chunks': get_documents()}
    except (requests.RequestException, ValueError):
        return {'status': 'error', 'student': 'student3', 'chunks': [],
                'error': 'Student 3 source API unavailable or invalid'}
