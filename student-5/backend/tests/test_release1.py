import release1
from flask import Flask


def make_client():
    app = Flask(__name__)
    app.register_blueprint(release1.release1_bp)
    return app.test_client()


def test_mcp_rejects_unapproved_tool(monkeypatch):
    monkeypatch.setenv("MCP_MODE", "true")
    response = make_client().post(
        "/api/mcp", json={"tool": "run_arbitrary_sql", "arguments": {}}
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "tool_not_allowed"


def test_mcp_can_be_disabled_for_ci(monkeypatch):
    monkeypatch.setenv("MCP_MODE", "false")
    response = make_client().post(
        "/api/mcp", json={"tool": "student5_find_campus_spaces", "arguments": {}}
    )
    assert response.status_code == 503
    assert response.get_json()["error"] == "mcp_disabled"


def test_rag_can_be_disabled_for_ci(monkeypatch):
    monkeypatch.setenv("RAG_MODE", "false")
    response = make_client().post("/api/rag", json={"query": "test query"})
    assert response.status_code == 503
    assert response.get_json()["error"] == "rag_disabled"
