# ASD Group 22 – Release 1

Release 1 extends the Group 22 Release 0 microservice application with one shared local MCP server, one shared local RAG service, and one shared local agentic validation loop.

## Student Features

- Student 1 – Project Management
- Student 2 – Skill Exchange
- Student 3 – Project Group Formation
- Student 4 – Skill Profile
- Student 5 – AI Campus Space Finder

## Architecture

Each student feature retains its containerised frontend, backend/API and database microservices.

The following services run locally outside Docker Compose:

- Ollama / local AI – `localhost:11434`
- Shared MCP server – `localhost:5100/mcp`
- Shared RAG server – `localhost:5003`
- Shared agentic validation loop

Containerised backends access local services through `host.docker.internal`.

## Shared Release 1 Services

- `ai-services/mcp-server/` – shared MCP server and feature tools
- `ai-services/rag-server/` – shared RAG pipeline and feature sources
- `ai-services/agentic-loop/` – shared Plan → Act → Observe → Adapt validator

Feature-specific integrations are separated into `studentX.py` modules under the MCP tools, RAG sources and agentic scenarios directories.

## Running the Application

Start the containerised feature application from the repository root:

```powershell
docker compose up -d --build

```

Ollama, the shared MCP server and shared RAG server run separately on the local host when AI, MCP and RAG functionality is required.

## Validation

The shared agentic validation loop supports MCP and RAG validation across all five student features.

Final integrated validation results:

- MCP mode – 11/11 scenarios passed
- RAG mode – 15/15 scenarios passed
- Combined – 26/26 scenarios passed

RAG validation covers retrieval, grounded responses with citations and confidence categories, and insufficient-context behaviour.

## CI/CD

Student-specific GitHub Actions workflows are located under `.github/workflows/student-*-ci.yml`.

The workflows build and validate the containerised feature microservices without depending on the locally hosted MCP and RAG services.
