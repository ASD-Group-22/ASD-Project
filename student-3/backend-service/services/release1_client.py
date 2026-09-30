"""Clients for the shared host services. Never start a server inside this backend."""
import asyncio
import json
import os
import requests


class ServiceError(Exception):
    pass


def enabled(name):
    return os.getenv(name, 'false').strip().lower() in ('true', '1', 'yes', 'on')


async def _mcp_call(tool, arguments):
    # Keep imports lazy: disabled modes must start without a running MCP server.
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    url = os.getenv('MCP_SERVER_URL', 'http://host.docker.internal:8100/mcp')
    async with streamable_http_client(url) as (reader, writer, _):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments=arguments)
            if result.isError:
                raise ServiceError('The shared MCP tool returned an error.')
            data = getattr(result, 'structuredContent', None)
            if data is None:
                blocks = [c.text for c in result.content if getattr(c, 'type', None) == 'text']
                data = json.loads('\n'.join(blocks))
            if not isinstance(data, dict) or data.get('status') != 'success':
                raise ServiceError('The shared MCP tool did not return a successful structured result.')
            return data


def call_mcp(tool, arguments):
    async def bounded():
        return await asyncio.wait_for(_mcp_call(tool, arguments), timeout=30)
    try:
        return asyncio.run(bounded())
    except Exception as exc:
        raise ServiceError('Shared MCP unavailable. Check registration, HTTP transport and MCP_SERVER_URL.') from exc


def call_rag(query, k):
    url = os.getenv('RAG_SERVER_URL', 'http://host.docker.internal:5003').rstrip('/')
    try:
        response = requests.post(url + '/answer', json={
            'query': query, 'k': k, 'caller': 'student3'}, timeout=(5, 150))
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise ServiceError('Shared RAG unavailable. Check RAG_SERVER_URL and the local RAG service.') from exc
    return validate_rag(data)


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
    if confidence not in ('High', 'Medium', 'Low', 'Unknown') or not isinstance(citations, list):
        raise ServiceError('Shared RAG must return citations and a confidence_category.')
    insufficient = (data.get('status') == 'insufficient_context'
                    or answer.strip().lower() in ('insufficient evidence.', 'insufficient context.', 'insufficient context'))
    if insufficient or not citations:
        return {'status': 'insufficient_context', 'answer': 'Insufficient context to answer this question.',
                'citations': [], 'confidence_category': 'Unknown',
                'retrieval_summary': data.get('retrieval_summary', {})}
    if any(not isinstance(c, dict) or not c.get('source_id') or not c.get('chunk_id') for c in citations):
        raise ServiceError('Shared RAG returned incomplete citation identifiers.')
    return {**data, 'status': 'success'}
