"""Student 5 shared adapter: capacity/facilities are hard constraints."""
from adapters import student5


def test_extract_group_size_whiteboard():
    parsed = student5._constraints("I need a quiet study space for 4 people with a whiteboard")
    assert parsed["min_capacity"] == 4
    assert parsed["noise_level"] == "quiet"
    assert "whiteboard" in parsed["facilities"]


def test_retrieve_only_verified_stored_spaces(monkeypatch):
    records = [
        {"space_id": 1, "space_name": "One-person room", "max_capacity": 1, "noise_level": "Quiet", "facilities": ["Whiteboard"]},
        {"space_id": 2, "space_name": "Group room", "max_capacity": 6, "noise_level": "Quiet", "facilities": ["Whiteboards", "Power Outlets"]},
        {"space_id": 3, "space_name": "Group room without board", "max_capacity": 6, "noise_level": "Quiet", "facilities": []},
    ]

    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return records

    monkeypatch.setattr(student5.requests, "get", lambda *args, **kwargs: Response())
    result = student5.gather_evidence("campus_space_recommendation", {
        "query": "quiet room for 4 people with whiteboard"
    })
    assert result["total_spaces_checked"] == 3
    assert result["evidence_count"] == 1
    assert result["allowed_output_references"] == ["space:2"]
    assert result["candidates"][0]["space_name"] == "Group room"
