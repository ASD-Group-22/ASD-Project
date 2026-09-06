STUDENT 3 - GROUP FORMATION
Recommends balanced groups using Student 4's live skill profiles and Ollama.
Uses Flask, SQLite, HTML/JavaScript and Docker.

START 
Run these commands from the ASD-Project root with Docker Desktop and Ollama running:
  ollama pull llama3.1:8b
  docker compose -f docker-compose.yml up -d --build student-3-frontend student-4-frontend home-page

The pull command is only needed if the model is not installed.
Use only the shared root docker-compose.yml.
If the old standalone Student 3 containers are running, stop them first to free 
ports 5000, 6000 and 8000.

PAGES
  Group dashboard: http://localhost:8000
  Skill profiles:  http://localhost:5006
  Team home page:  http://localhost:3000

USE
1. Create or update profiles in the Skill Profile page.
2. Add project skill requirements for a subject in the group dashboard.
3. Open Recommendations and load the profiles.
4. Choose a target group size and optionally enter student IDs.
5. Request groups and review the reasoning and skill gaps.

Blank student IDs includes all profiles. Subject enrolment is not automatically checked.

Recommendations are proposals; they do not automatically save or finalise groups.

PROMPT AND MODEL
Prompt: student-3/prompts/group_service/implementation/group_balance_prompt.txt
The shared Compose file mounts this folder at /prompts.
Default model: llama3.1:8b. Override with STUDENT3_OLLAMA_MODEL.
Ollama runs on the host computer separately from the shared Compose stack.

TESTS AND CI
From the project root, in a Python environment:
  python -m pip install -r student-3/backend-service/requirements.txt pytest
  python -m pytest student-3/tests -v

Workflow: .github/workflows/student-3-ci.yml

It runs tests, validates root Compose, builds the required images and checks profile access.

Results and container logs are uploaded as a workflow artifact.
Automated tests simulate Ollama. Test real model responses locally before demonstrating.