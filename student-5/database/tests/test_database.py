import os
import tempfile

import pytest

db_fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(db_fd)
os.environ["DATABASE_PATH"] = db_path
import app as db_app


@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(os.environ["DATABASE_PATH"]):
        os.remove(os.environ["DATABASE_PATH"])
    db_app.init_db()
    db_app.app.config.update(TESTING=True)
    yield


def test_seed_has_at_least_ten_records():
    client = db_app.app.test_client()
    response = client.get("/spaces")
    assert response.status_code == 200
    assert len(response.get_json()) >= 10


def test_full_crud():
    client = db_app.app.test_client()
    payload = {
        "space_name": "Test Space", "building": "Building 99", "building_level": "1",
        "room_number": "T1", "max_capacity": 3, "space_type": "Study",
        "noise_level": "Quiet", "facilities": ["Wi-Fi"], "accessibility": "Yes",
        "opening_time": "08:00", "closing_time": "18:00", "description": "Test", "image_url": ""
    }
    created = client.post("/spaces", json=payload)
    assert created.status_code == 201
    sid = created.get_json()["space_id"]
    assert client.get(f"/spaces/{sid}").status_code == 200
    updated = client.put(f"/spaces/{sid}", json={"max_capacity": 5})
    assert updated.get_json()["max_capacity"] == 5
    assert client.delete(f"/spaces/{sid}").status_code == 200
    assert client.get(f"/spaces/{sid}").status_code == 404
