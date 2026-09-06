import os
import requests


DATABASE_SERVICE_URL = os.getenv(
    "DATABASE_SERVICE_URL",
    "http://localhost:5004"
)


def create_profile(data):
    response = requests.post(
        f"{DATABASE_SERVICE_URL}/profiles",
        json=data,
        timeout=10
    )

    return response.json(), response.status_code


def get_profile(profile_id):
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/profiles/{profile_id}",
        timeout=10
    )

    return response.json(), response.status_code


def update_profile(profile_id, data):
    response = requests.put(
        f"{DATABASE_SERVICE_URL}/profiles/{profile_id}",
        json=data,
        timeout=10
    )

    return response.json(), response.status_code


def delete_profile(profile_id):
    response = requests.delete(
        f"{DATABASE_SERVICE_URL}/profiles/{profile_id}",
        timeout=10
    )

    return response.json(), response.status_code

def get_profile_by_student_id(student_id):
    response = requests.get(
        f"{DATABASE_SERVICE_URL}/profiles/student/{student_id}",
        timeout=10
    )

    return response.json(), response.status_code

#ADDED FOR STUDENT 3 TO LIST ALL PROFILES
def list_profiles():
    response = requests.get(f'{DATABASE_SERVICE_URL}/profiles', timeout=10)
    return response.json(), response.status_code