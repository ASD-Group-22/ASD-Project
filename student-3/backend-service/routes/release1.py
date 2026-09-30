"""Student 3 UI -> backend -> shared host MCP/RAG services."""
from flask import Blueprint, jsonify, request
from services.release1_client import enabled, call_mcp, call_rag, ServiceError

r1_bp = Blueprint('release1', __name__)


@r1_bp.get('/status')
def status():
    return jsonify({'mcp_enabled': enabled('MCP_ENABLED'), 'rag_enabled': enabled('RAG_ENABLED')})


@r1_bp.post('/mcp')
def mcp():
    if not enabled('MCP_ENABLED'):
        return jsonify(error='MCP mode is disabled until shared integration is configured.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Send a JSON object.'), 400
    tool = data.get('tool')
    # No arbitrary tool names, URLs, writes, shell commands or database access.
    arguments = {}
    if tool == 'student3_group_requirements':
        subject = data.get('subject')
        if not isinstance(subject, str) or not 1 <= len(subject.strip()) <= 100:
            return jsonify(error='Enter a subject of 1 to 100 characters.'), 400
        arguments['subject'] = subject.strip()
    elif tool != 'student3_list_groups':
        return jsonify(error='Unsupported Student 3 tool.'), 400
    try:
        return jsonify(call_mcp(tool, arguments))
    except ServiceError as exc:
        return jsonify(error=str(exc)), 503


@r1_bp.post('/rag')
def rag():
    if not enabled('RAG_ENABLED'):
        return jsonify(error='RAG mode is disabled until shared integration is configured.'), 503
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Send a JSON object.'), 400
    query, k = data.get('query'), data.get('k', 5)
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 1000:
        return jsonify(error='Enter a question of 1 to 1000 characters.'), 400
    if type(k) is not int or not 1 <= k <= 10:
        return jsonify(error='k must be an integer from 1 to 10.'), 400
    try:
        return jsonify(call_rag(query.strip(), k))
    except ServiceError as exc:
        return jsonify(error=str(exc)), 503
