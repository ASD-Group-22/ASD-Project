import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "student-3/backend-service"))

import group_recommendations as service
from app import create_app


def profiles(count=10):
    return [
        {
            "student_id": i,
            "profile_id": i,
            "skills": [
                {
                    "skill_name": " Python ",
                    "skill_level": "Advanced" if i % 2 else "Beginner",
                    "strength": "Problem solving",
                    "weakness": "Testing",
                }
            ],
        }
        for i in range(1, count + 1)
    ]


def answer(ids=None):
    if ids is None:
        ids = [list(range(1, 6)), list(range(6, 11))]

    return {
        "groups": [
            {
                "student_ids": group,
                "reasoning": "Complementary recorded skills.",
            }
            for group in ids
        ]
    }


@pytest.fixture
def client(monkeypatch):
    def get(url):
        if "/requirements/" in url:
            return {
                "python": {
                    "level": "intermediate",
                    "amount": "extensive",
                },
                "sql": {
                    "level": "beginner",
                    "amount": "little",
                },
            }
        return profiles()

    monkeypatch.setattr(service, "get_json", get)
    return create_app().test_client()


def ollama(monkeypatch, *responses):
    post = Mock(
        side_effect=[
            Mock(
                json=Mock(
                    return_value={
                        "message": {"content": json.dumps(response)}
                    }
                )
            )
            for response in responses
        ]
    )
    monkeypatch.setattr(service.requests, "post", post)
    return post


@pytest.mark.parametrize(
    "route",
    [
        "/ai/group-recommendation",
        "/ui/ai/group-recommendation",
    ],
)

def test_live_profiles_and_coverage(client, monkeypatch, route):
    post = ollama(monkeypatch, answer())
    response = client.post(route, json={"subject": "ASD"})

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["students"]) == 10
    assert data["students"][0]["skills"] == {"python": 3}
    assert (
        data["recommendation"]["groups"][0]["unmet_requirements"]
        == ["sql"]
    )

    assert len(data["recommendation"]["warnings"]) == 2
    context = json.loads(
        post.call_args.kwargs["json"]["messages"][1]["content"]
    )

    assert (
        context["students"][0]["skill_details"][0]["strength"]
        == "Problem solving"
    )

    assert context["group_sizes"] == [5, 5]


def test_duplicate_ids_trigger_repair(client, monkeypatch):
    invalid = answer(
        [[1, 1, 3, 4, 5], [6, 7, 8, 9, 10]]
    )

    post = ollama(monkeypatch, invalid, answer())
    response = client.post(
        "/ai/group-recommendation",
        json={"subject": "ASD"},
    )

    assert response.status_code == 200
    assert response.json["attempts"] == 2
    assert post.call_count == 2


@pytest.mark.parametrize(
    "bad",
    [
        answer([[1, 2, 3, 4, 99], [6, 7, 8, 9, 10]]),
        answer([[1, 2, 3], [4, 5, 6]]),
        answer([[True, 2, 3, 4, 5], [6, 7, 8, 9, 10]]),
        {"groups": []},
        {"groups": [None, None]},
        answer([[1, 2, 3, 4], [5, 6, 7, 8, 9, 10]]),
    ],
)
def test_invalid_groups_never_succeed(client, monkeypatch, bad):
    ollama(monkeypatch, bad, bad)

    response = client.post(
        "/ai/group-recommendation",
        json={"subject": "ASD"},
    )

    assert response.status_code == 502


def test_candidate_selection(client, monkeypatch):
    post = ollama(monkeypatch, answer([[2, 4, 8]]))

    response = client.post(
        "/ai/group-recommendation",
        json={
            "subject": "ASD",
            "student_ids": [2, 4, 8],
        },
    )

    assert response.status_code == 200
    assert [
        student["student_id"]
        for student in response.json["students"]
    ] == [2, 4, 8]

    context = json.loads(
        post.call_args.kwargs["json"]["messages"][1]["content"]
    )

    assert len(context["students"]) == 3


@pytest.mark.parametrize(
    "data,status",
    [
        (None, 400),
        ({}, 400),
        ({"subject": "ASD", "group_size": True}, 400),
        ({"subject": "ASD", "group_size": 6}, 400),
        ({"subject": "ASD", "student_ids": [999]}, 422),
        ({"subject": "ASD", "student_ids": [1, 1, 2]}, 400),
        ({"subject": "ASD", "student_ids": [1, 2]}, 422),
    ],
)

def test_input_validation(client, data, status):
    response = client.post(
        "/ai/group-recommendation",
        json=data,
    )

    assert response.status_code == status


def test_ollama_unavailable(client, monkeypatch):
    monkeypatch.setattr(
        service.requests,
        "post",
        Mock(side_effect=requests.Timeout()),
    )

    response = client.post(
        "/ai/group-recommendation",
        json={"subject": "ASD"},
    )

    assert response.status_code == 503


def test_profile_service_unavailable(monkeypatch):
    monkeypatch.setattr(
        service.requests,
        "get",
        Mock(side_effect=requests.ConnectionError()),
    )

    response = create_app().test_client().get("/ai/profiles")

    assert response.status_code == 503


def test_empty_requirements(client, monkeypatch):
    monkeypatch.setattr(service, "get_json", lambda url: {})

    response = client.post(
        "/ai/group-recommendation",
        json={"subject": "ASD"},
    )

    assert response.status_code == 422


def test_group_sizes_include_every_student():
    for count in range(3, 101):
        for target in (3, 4, 5):
            sizes = service.group_sizes(count, target)

            assert sum(sizes) == count
            assert min(sizes) >= 3
            assert max(sizes) <= 5
            assert max(sizes) - min(sizes) <= 1


def test_latest_profile_list_uses_real_sqlite(
    tmp_path,
    monkeypatch,
):

    spec = importlib.util.spec_from_file_location(
        "skill_db_app",
        ROOT / "student-4/database/app.py",
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    spec = importlib.util.spec_from_file_location(
        "skill_db_init",
        ROOT / "student-4/database/init_db.py",
    )

    init = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(init)
    db_path = str(tmp_path / "profiles.db")

    monkeypatch.setattr(init, "DATABASE_PATH", db_path)
    monkeypatch.setattr(init, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(module, "DATABASE_PATH", db_path)

    init.init_db()
    client = module.app.test_client()

    assert len(client.get("/profiles").json) == 10

    created = client.post(
        "/profiles",
        json={
            "student_id": 1,
            "skills": [
                {
                    "skill_name": "SQL",
                    "skill_level": "Advanced",
                }
            ],
        },
    )

    assert created.status_code == 201

    listed = client.get("/profiles").json

    assert len(listed) == 10

    # Find Student 1 by identity, not position in the list.
    matches = [
        profile
        for profile in listed
        if profile["student_id"] == 1
    ]

    assert len(matches) == 1
    student_one = matches[0]

    assert student_one["profile_id"] == created.json["profile_id"]
    assert student_one["skills"][0]["skill_name"] == "SQL"
    assert client.get("/profiles/student/1").json == student_one

    updated_response = client.put(
        f'/profiles/{created.json["profile_id"]}',
        json={
            "skills": [
                {
                    "skill_name": "Git",
                    "skill_level": "Beginner",
                }
            ]
        },
    )

    assert updated_response.status_code == 200

    updated_profiles = client.get("/profiles").json
    updated = next(
        profile
        for profile in updated_profiles
        if profile["student_id"] == 1
    )

    assert updated["profile_id"] == created.json["profile_id"]
    assert updated["skills"][0]["skill_name"] == "Git"