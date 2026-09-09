import json
import os
import urllib.request
import urllib.error

from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
STUDENT_DIR = BASE_DIR.parent
PROJECT_DIR = STUDENT_DIR.parent

PROMPTS_DIR = BASE_DIR / "prompts"
LOGS_DIR = BASE_DIR / "logs"


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:0.5b"
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "http://localhost:5004"
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:5005"
)


def load_prompt(filename):

    path = PROMPTS_DIR / filename

    return path.read_text(
        encoding="utf-8"
    )


def read_file(path):

    try:

        return path.read_text(
            encoding="utf-8"
        )

    except Exception as error:

        return f"Could not read file: {error}"


def get_url(url):

    try:

        with urllib.request.urlopen(
            url,
            timeout=10
        ) as response:

            body = response.read().decode(
                "utf-8"
            )

            return {
                "status": response.status,
                "body": body
            }

    except urllib.error.HTTPError as error:

        return {
            "status": error.code,
            "body": error.read().decode(
                "utf-8"
            )
        }

    except Exception as error:

        return {
            "status": "FAILED",
            "body": str(error)
        }


def call_ollama(system_prompt, prompt):

    payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 350,
            "repeat_penalty": 1.2
        }
    }

    request_data = json.dumps(
        payload
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=request_data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=300
    ) as response:

        result = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

    return result.get(
        "response",
        ""
    )


def collect_database_evidence():

    evidence = {
        "database_health": get_url(
            f"{DATABASE_URL}/"
        ),

        "student_1": get_url(
            f"{BACKEND_URL}/api/profiles/student/1"
        ),

        "student_4": get_url(
            f"{BACKEND_URL}/api/profiles/student/4"
        ),

        "student_10": get_url(
            f"{BACKEND_URL}/api/profiles/student/10"
        ),

        "database_code": read_file(
            STUDENT_DIR
            / "database"
            / "app.py"
        ),

        "database_schema": read_file(
            STUDENT_DIR
            / "database"
            / "init_db.py"
        )
    }

    return json.dumps(
        evidence,
        indent=2
    )


def collect_endpoint_evidence():

    evidence = {
        "backend_health": get_url(
            f"{BACKEND_URL}/"
        ),

        "profile_by_student": get_url(
            f"{BACKEND_URL}/api/profiles/student/4"
        ),

        "backend_code": read_file(
            STUDENT_DIR
            / "backend"
            / "app.py"
        ),

        "database_api_client": read_file(
            STUDENT_DIR
            / "backend"
            / "services"
            / "database_api.py"
        )
    }

    return json.dumps(
        evidence,
        indent=2
    )


def collect_architecture_evidence():

    backend_code = read_file(
        STUDENT_DIR
        / "backend"
        / "app.py"
    )

    evidence = {
        "backend_direct_sqlite_access":
            "sqlite3.connect" in backend_code,

        "database_api_client": read_file(
            STUDENT_DIR
            / "backend"
            / "services"
            / "database_api.py"
        ),

        "frontend_dockerfile": read_file(
            STUDENT_DIR
            / "frontend"
            / "Dockerfile"
        ),

        "backend_dockerfile": read_file(
            STUDENT_DIR
            / "backend"
            / "Dockerfile"
        ),

        "database_dockerfile": read_file(
            STUDENT_DIR
            / "database"
            / "Dockerfile"
        )
    }

    return json.dumps(
        evidence,
        indent=2
    )


def collect_devops_evidence():

    evidence = {
        "student_4_ci": read_file(
            PROJECT_DIR
            / ".github"
            / "workflows"
            / "student-4-ci.yml"
        ),

        "root_docker_compose": read_file(
            PROJECT_DIR
            / "docker-compose.yml"
        )
    }

    return json.dumps(
        evidence,
        indent=2
    )


def plan(target):

    print()
    print("=" * 70)
    print(f"[{target}][PLAN]")
    print("=" * 70)

    print(
        f"Review Student 4 {target} implementation."
    )


def act(target, evidence):

    print()
    print(f"[{target}][ACT]")
    print("Running implementation agent...")

    system_prompt = load_prompt(
        "implementation_system_prompt.txt"
    )

    task_prompt = load_prompt(
        "implementation_task_prompt.txt"
    )

    task_prompt = task_prompt.replace(
        "{{REVIEW_TARGET}}",
        target
    )

    task_prompt = task_prompt.replace(
        "{{EVIDENCE}}",
        evidence
    )

    response = call_ollama(
        system_prompt,
        task_prompt
    )

    print()
    print("IMPLEMENTATION AGENT:")
    print(response)

    return response


def observe(target, evidence, implementation_response):

    print()
    print(f"[{target}][OBSERVE]")
    print("Running independent review agent...")

    system_prompt = load_prompt(
        "review_system_prompt.txt"
    )

    task_prompt = load_prompt(
        "review_task_prompt.txt"
    )

    task_prompt = task_prompt.replace(
        "{{REVIEW_TARGET}}",
        target
    )

    task_prompt = task_prompt.replace(
        "{{EVIDENCE}}",
        evidence
    )

    task_prompt = task_prompt.replace(
        "{{IMPLEMENTATION_RESPONSE}}",
        implementation_response
    )

    response = call_ollama(
        system_prompt,
        task_prompt
    )

    print()
    print("REVIEW AGENT:")
    print(response)

    return response


def adapt():

    print()
    print("[ADAPT]")
    print("1 - Accept")
    print("2 - Partially Accept")
    print("3 - Reject")

    choice = input(
        "Choose adaptation decision: "
    ).strip()

    if choice == "1":

        return (
            "ACCEPTED - Recommendation will be applied."
        )

    elif choice == "2":

        return (
            "PARTIALLY ACCEPTED - Selected improvements will be applied."
        )

    elif choice == "3":

        return (
            "REJECTED - Current implementation retained."
        )

    return "No valid adaptation decision."


def save_log(
    target,
    evidence,
    implementation_response,
    review_response,
    adaptation
):

    LOGS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    path = (
        LOGS_DIR
        / f"{target.lower()}_{timestamp}.txt"
    )

    content = f"""
STUDENT 4 SKILL PROFILE SERVICE
AGENTIC AI REVIEW RECORD

TARGET:
{target}

==================================================
PLAN
==================================================

Review the Student 4 {target} implementation.

==================================================
ACT
==================================================

{implementation_response}

==================================================
OBSERVE
==================================================

{review_response}

==================================================
ADAPT
==================================================

{adaptation}

==================================================
EVIDENCE
==================================================

{evidence}
"""

    path.write_text(
        content,
        encoding="utf-8"
    )

    print()
    print(f"Log saved to: {path}")


def run_review(target):

    plan(target)

    if target == "Database":

        evidence = collect_database_evidence()

    elif target == "Endpoints":

        evidence = collect_endpoint_evidence()

    elif target == "Architecture":

        evidence = collect_architecture_evidence()

    elif target == "DevOps":

        evidence = collect_devops_evidence()

    else:

        print("Unknown review target.")
        return

    implementation_response = act(
        target,
        evidence
    )

    review_response = observe(
        target,
        evidence,
        implementation_response
    )

    adaptation = adapt()

    print()
    print(adaptation)

    save_log(
        target,
        evidence,
        implementation_response,
        review_response,
        adaptation
    )

    print()
    print(f"[{target}][LOOP COMPLETE]")


def main():

    while True:

        print()
        print("=" * 70)
        print(
            "STUDENT 4 - SKILL PROFILE AGENTIC REVIEW"
        )
        print("=" * 70)

        print("1 - Database")
        print("2 - Endpoints")
        print("3 - Architecture")
        print("4 - DevOps")
        print("5 - Run All")
        print("0 - Exit")

        choice = input(
            "Choose a review target: "
        ).strip()

        if choice == "1":

            run_review("Database")

        elif choice == "2":

            run_review("Endpoints")

        elif choice == "3":

            run_review("Architecture")

        elif choice == "4":

            run_review("DevOps")

        elif choice == "5":

            for target in [
                "Database",
                "Endpoints",
                "Architecture",
                "DevOps"
            ]:

                run_review(target)

        elif choice == "0":

            print("Agentic review stopped.")
            break

        else:

            print("Invalid option.")


if __name__ == "__main__":

    main()