import unittest
from unittest.mock import patch

import app as backend


class ProfileEndpointTests(unittest.TestCase):
    def setUp(self):
        backend.app.config["TESTING"] = True
        self.client = backend.app.test_client()

    def test_create_profile_success(self):
        payload = {
            "student_id": 4,
            "skills": [{
                "skill_name": "Python",
                "level": "Intermediate",
                "strength": "Problem solving",
                "weakness": "Advanced libraries",
            }],
        }
        expected = {"profile_id": 42}

        with patch.object(
            backend, "create_profile", return_value=(expected, 201)
        ) as database:
            response = self.client.post("/api/profiles", json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), expected)
        database.assert_called_once_with(payload)

    def test_create_profile_rejects_empty_data(self):
        with patch.object(backend, "create_profile") as database:
            response = self.client.post("/api/profiles", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "No data provided"})
        database.assert_not_called()

    def test_get_profile_success(self):
        expected = {"profile_id": 42, "student_id": 4, "skills": []}

        with patch.object(
            backend, "get_profile", return_value=(expected, 200)
        ) as database:
            response = self.client.get("/api/profiles/42")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), expected)
        database.assert_called_once_with(42)

    def test_get_profile_not_found(self):
        expected = {"error": "Profile not found"}

        with patch.object(
            backend, "get_profile", return_value=(expected, 404)
        ) as database:
            response = self.client.get("/api/profiles/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), expected)
        database.assert_called_once_with(999999)


if __name__ == "__main__":
    unittest.main()