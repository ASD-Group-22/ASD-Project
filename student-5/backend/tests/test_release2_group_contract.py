"""Contract tests for the Group 22 shared Multi-Agent HTTP API."""
from flask import Flask
import release2


def client():
    application = Flask(__name__)
    application.register_blueprint(release2.bp)
    return application.test_client()


def test_create_workflow_uses_group_schema(monkeypatch):
    monkeypatch.setattr(release2, "MULTI_AGENT_MODE", True)
    sent = []

    class Reply:
        status_code = 201
        def json(self):
            return {"workflow_id": "1234", "status": "awaiting_human_review"}

    def fake_request(method, url, json=None, timeout=None):
        sent.append((method, url, json))
        return Reply()

    monkeypatch.setattr(release2.requests, "request", fake_request)
    response = client().post("/api/multi-agent/workflows", json={"query": "quiet room for 4 with whiteboard"})
    assert response.status_code == 201
    assert sent[0][0] == "POST"
    assert sent[0][1].endswith("/workflows")
    assert sent[0][2] == {
        "feature": "student5",
        "task_type": "campus_space_recommendation",
        "user_request": "quiet room for 4 with whiteboard",
        "context": {"query": "quiet room for 4 with whiteboard"},
    }


def test_human_review_uses_group_notes_and_decision(monkeypatch):
    monkeypatch.setattr(release2, "MULTI_AGENT_MODE", True)
    sent = []

    class Reply:
        status_code = 200
        def json(self):
            return {"status": "partial_accept"}

    def fake_request(method, url, json=None, timeout=None):
        sent.append(json)
        return Reply()

    monkeypatch.setattr(release2.requests, "request", fake_request)
    workflow_id = "00000000-0000-4000-8000-000000000001"
    response = client().post(
        f"/api/multi-agent/workflows/{workflow_id}/review",
        json={"decision": "partially_accept", "comment": "Only one room is suitable"},
    )
    assert response.status_code == 200
    assert sent == [{"decision": "partial_accept", "notes": "Only one room is suitable"}]

def test_correct_human_review_uses_shared_endpoint_and_correction(monkeypatch):
    monkeypatch.setattr(release2, "MULTI_AGENT_MODE", True)
    sent = []

    class Reply:
        status_code = 200

        def json(self):
            return {"status": "completed"}

    def fake_request(method, url, json=None, timeout=None):
        sent.append((method, url, json))
        return Reply()

    monkeypatch.setattr(release2.requests, "request", fake_request)

    workflow_id = "00000000-0000-4000-8000-000000000001"

    response = client().post(
        f"/api/multi-agent/workflows/{workflow_id}/review",
        json={
            "decision": "correct",
            "comment": "Adjusted the recommendation.",
            "corrected_response": "Use Building 11 Room 204 instead.",
        },
    )

    assert response.status_code == 200
    assert sent[0][0] == "POST"
    assert sent[0][1].endswith(
        f"/workflows/{workflow_id}/human-review"
    )
    assert sent[0][2] == {
        "decision": "correct",
        "notes": "Adjusted the recommendation.",
        "corrected_response": "Use Building 11 Room 204 instead.",
    }
