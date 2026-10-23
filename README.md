# ASD Group 22 - Release 2

Final integrated Release 2 application for UTS 41026 Advanced Software Development with Agentic AI.

Release 2 extends the completed Release 1 system with a shared local Multi-Agent Server, Planner, Worker and Reviewer agents, human review, Release 2 agentic-loop review modes, pre-commit security testing, post-commit endpoint CI/CD testing, and Microsoft Azure deployment.

## Student Features

1. Student 1 - Project Management
2. Student 2 - Skill Exchange
3. Student 3 - Project Group Formation
4. Student 4 - Skill Profile
5. Student 5 - AI Campus Space Finder

Each feature maintains its own frontend, backend/API and database microservices.

## Local Architecture

Student microservices run through the shared root `docker-compose.yml`.

The following shared AI services run locally outside Docker Compose:

- Ollama - `http://localhost:11434`
- MCP Server - `http://localhost:5100/mcp`
- RAG Server - `http://localhost:5003`
- Multi-Agent Server - `http://localhost:5101`
- Shared agentic loop - `ai-services/agentic-loop/`

Containerised backends access the local shared services through `host.docker.internal`.

## Release 2 Multi-Agent Flow

`Frontend UI -> Backend/API -> Multi-Agent Server -> Planner -> Worker -> Reviewer -> Human Review -> Backend/API -> Frontend UI`

The shared Multi-Agent Server contains adapters for all five features:

- `student1`
- `student2`
- `student3`
- `student4`
- `student5`

Default local models:

- Planner - `qwen3:8b`
- Worker - `qwen3:8b`
- Reviewer - `llama3.1:8b`

Human review supports approval, correction, partial acceptance and rejection.

## Running the Local Application

From the repository root:

`docker compose up -d --build`

Unified home page:

`http://localhost:3000`

Feature frontends:

| Feature | Frontend |
| --- | --- |
| Student 1 - Project Management | `http://localhost:3001` |
| Student 2 - Skill Exchange | `http://localhost:8202` |
| Student 3 - Group Formation | `http://localhost:8000` |
| Student 4 - Skill Profile | `http://localhost:5006` |
| Student 5 - Campus Space Finder | `http://localhost:8005` |

## Shared Agentic AI Services

Release 0 and Release 1 functionality is retained:

- AI-Mode with Ollama
- shared MCP Server
- shared RAG Server
- grounded RAG responses with citations and confidence handling
- shared Plan -> Act -> Observe -> Adapt agentic loop

Release 2 adds:

- shared Multi-Agent Server
- Planner Agent
- Worker Agent
- Reviewer Agent
- Human Review
- Multi-Agent Workflow Review
- Testing Report Review
- Cloud Deployment Report Review

## Security and Testing

Local pre-commit validation uses:

- Ruff security and correctness rules
- detect-secrets
- pip-audit

Per-student testing reports and raw evidence are stored under:

`reports/release2/`

Each student's GitHub Actions workflow tests two assigned backend/API endpoint functions.

Final validated software-changing commit:

`9d623239f4e30840b00e5ef221702114317a519c`

Successful final integration CI:

`39973124752`

Successful final student workflow runs:

| Student | Run |
| --- | ---: |
| Student 1 | `39972587866` |
| Student 2 | `39973749169` |
| Student 3 | `39972587659` |
| Student 4 | `39972587459` |
| Student 5 | `39972587538` |

See `docs/release2-evidence-index.md` for detailed evidence locations.

## Cloud Deployment

The integrated group application was deployed using Microsoft Azure Container Apps.

The required cloud baseline keeps local Agentic AI integrations disabled by default:

- AI-Mode - disabled
- MCP - disabled
- RAG - disabled
- Multi-Agent - disabled

Core frontend, backend/API, database and CRUD functionality remain operational in the cloud deployment.

Cloud deployment artefacts:

- `.github/workflows/cloud-deployment.yml`
- `scripts/cloud/azure/`
- `reports/release2/cloud-deployment-report.md`
- `reports/release2/cloud-deployment-results.md`

## Repository Structure

- `.github/workflows/` - GitHub Actions CI/CD workflows
- `ai-services/` - MCP, RAG, Multi-Agent and agentic-loop services
- `docs/` - final documentation and Release 2 evidence index
- `reports/release2/` - testing, deployment and evidence reports
- `scripts/cloud/azure/` - reusable Azure deployment scripts
- `shared/` - unified home page and shared resources
- `student-1/` - Project Management
- `student-2/` - Skill Exchange
- `student-3/` - Project Group Formation
- `student-4/` - Skill Profile
- `student-5/` - Campus Space Finder
- `docker-compose.yml` - integrated local microservice deployment

## Release 2 Evidence

See:

`docs/release2-evidence-index.md`
