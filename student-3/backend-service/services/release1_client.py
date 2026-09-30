"""Clients for the shared host services. Never start a server inside this backend."""
import asyncio
import json
import os
import requests


class ServiceError(Exception):
    pass


def enabled(name):
    return os.getenv(name, 'false').strip().lower() in ('true', '1', 'yes', 'on')


def decode_tool_result(result):
    if getattr(result, 'is_error', False):
        raise ServiceError('The shared MCP tool returned an error.')
    data = getattr(result, 'structured_content', None)
    if not isinstance(data, dict):
        data = None
        for block in getattr(result, 'content', []):
            try:
                candidate = json.loads(getattr(block, 'text', ''))
                if isinstance(candidate, dict):
                    data = candidate
                    break
            except (ValueError, TypeError):
                continue
    if not isinstance(data, dict) or data.get('status') != 'success':
        raise ServiceError('MCP tool unsuccessful: ' + str((data or {}).get('error', 'invalid structured result')))
    return data


async def _mcp_call(tool, arguments):
    from mcp import Client
    # Use Student 2's configuration names; accept the earlier names during migration.
    url = os.getenv('MCP_URL') or os.getenv('MCP_SERVER_URL', 'http://host.docker.internal:5100/mcp')
    async with Client(url) as client:
        result = await client.call_tool(tool, {**arguments, 'caller': 'student-3-backend'})
        return decode_tool_result(result)


def call_mcp(tool, arguments):
    async def bounded():
        return await asyncio.wait_for(_mcp_call(tool, arguments), timeout=30)
    try:
        return asyncio.run(bounded())
    except Exception as exc:
        raise ServiceError('Shared MCP unavailable. Check registration, HTTP transport and MCP_URL.') from exc


def rag_request(action, query=None, k=5):
    if action not in ('answer', 'retrieve', 'refresh'):
        raise ServiceError('Unsupported RAG operation.')
    url = (os.getenv('RAG_SERVICE_URL') or os.getenv('RAG_SERVER_URL', 'http://host.docker.internal:5003')).rstrip('/')
    payload = {'caller': 'student-3-backend'}
    if action != 'refresh':
        payload.update(query=query, k=k)
    try:
        timeout = float(os.getenv('RAG_TIMEOUT_SECONDS', '180'))
        if not 1 <= timeout <= 600:
            raise ValueError('Invalid timeout')
        response = requests.post(url + '/' + action, json=payload, timeout=(5, timeout))
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ServiceError('Shared RAG unavailable. Check RAG_SERVICE_URL, timeout and the local service.') from exc
    if action == 'answer':
        return validate_rag(data)
    if not isinstance(data, dict) or data.get('status') != 'success':
        raise ServiceError('Shared RAG operation failed.')
    if action == 'retrieve' and not isinstance(data.get('results'), list):
        raise ServiceError('Shared RAG returned invalid retrieval results.')
    return data


def call_rag(query, k):
    return rag_request('answer', query, k)


def validate_rag(data):
    """Validate response shape; this does not prove factual grounding."""
    if not isinstance(data, dict) or data.get('status') not in ('success', 'insufficient_context'):
        raise ServiceError('Shared RAG returned an unsuccessful response.')
    answer = data.get('answer')
    citations = data.get('citations')
    confidence = data.get('confidence_category')
    if not isinstance(answer, str) or not answer.strip():
        raise ServiceError('Shared RAG returned no answer.')
    if answer.lower().startswith('ollama unavailable:'):
        raise ServiceError('The shared RAG model is unavailable.')
    if confidence not in ('High', 'Medium', 'Low', 'Unknown', 'Insufficient') or not isinstance(citations, list):
        raise ServiceError('Shared RAG must return citations and a confidence_category.')
    insufficient = (data.get('status') == 'insufficient_context'
                    or confidence == 'Insufficient'
                    or answer.strip().lower() in ('insufficient evidence.', 'insufficient context.', 'insufficient context'))
    if insufficient or not citations:
        return {'status': 'insufficient_context', 'answer': 'Insufficient context.',
                'citations': [], 'confidence_category': 'Insufficient',
                'retrieval_summary': data.get('retrieval_summary', {})}
    if any(not isinstance(c, dict) or not c.get('source_id') or not c.get('chunk_id') for c in citations):
        raise ServiceError('Shared RAG returned incomplete citation identifiers.')
    return {**data, 'status': 'success'}
