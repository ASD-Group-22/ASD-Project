# Student 2 - Skill Exchange Service - Release 1

## Overview

The Skill Exchange Service allows students to create and manage listings for skills they can offer and skills they want to learn.

The original Release 0 functionality remains available, including normal CRUD operations, deterministic candidate filtering, and AI-assisted matching. Release 1 extends the feature with access to the shared local MCP and RAG services through the Student 2 backend/API.

## Release 1 Functionality

The Student 2 feature provides four frontend modes:

- Normal UI - create, update, search, deactivate, and manage Skill Exchange listings.
- AI Mode - retains the Release 0 AI-assisted matching workflow using Plan, Act, Observe, and Adapt stages.
- MCP Mode - invokes Student 2 tools through the shared local MCP server.
- RAG Mode - retrieves Skill Exchange context and generates grounded answers through the shared local RAG server.

The existing Student 2 AI Mode is separate from the shared Release 1 agentic-loop service.

## Architecture

~~~text
Browser
  |
  v
Student 2 frontend microservice
  |
  | HTTP
  v
Student 2 Flask backend/API microservice
  |
  +--> Student 2 database API --> SQLite
  |
  +--> Host Ollama
  |      +--> Qwen main model
  |      +--> Llama review model
  |
  +--> Shared local MCP server
  |      localhost:5100/mcp
  |
  +--> Shared local RAG server
         localhost:5003
~~~

The frontend does not access MCP or RAG directly. Requests are sent through the Student 2 backend/API.

The shared MCP server, shared RAG server, Ollama runtime, and shared Release 1 agentic-loop service are local services outside the Student 2 Docker Compose stack.

## Docker Services

| Service | Host Port | Container Port |
| --- | ---: | ---: |
| Frontend | 8202 | 80 |
| Backend/API | 5202 | 5001 |
| Database API | 5302 | 5002 |

The database service stores Skill Exchange records in SQLite using the persistent `student_2_skill_exchange_data` Docker volume.

## Environment Configuration

Configuration defaults are provided in `.env.example`.

Important Release 1 settings are:

~~~text
AI_ENABLED=true
MCP_ENABLED=true
MCP_URL=http://host.docker.internal:5100/mcp
RAG_ENABLED=true
RAG_SERVICE_URL=http://host.docker.internal:5003
~~~

The backend reaches services running on the host through `host.docker.internal`.

The local Ollama defaults are:

~~~text
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_MODEL=qwen3:8b
OLLAMA_REVIEW_MODEL=llama3.1:8b
ENABLE_REVIEW_MODEL=true
~~~

## Running Student 2 Locally

From the repository root:

~~~powershell
docker compose -f .\student-2\docker-compose.yml up -d --build
~~~

Open the frontend at:

~~~text
http://localhost:8202
~~~

Normal UI uses the containerised Student 2 services.

AI Mode additionally requires the configured host Ollama runtime and models.

MCP Mode requires the shared local MCP server on port `5100`.

RAG Mode requires the shared local RAG server on port `5003`.

## MCP Integration

Student 2 registers the following tools with the shared MCP server:

- `student2_search_skills`
- `student2_get_listing`

The MCP request flow is:

~~~text
Frontend
  -> Student 2 backend/API
  -> shared MCP server
  -> registered Student 2 tool
  -> structured result
  -> Student 2 backend/API
  -> frontend
~~~

The browser does not communicate directly with the MCP server.

## RAG Integration

Student 2 contributes current Skill Exchange data to the shared enterprise RAG corpus.

The RAG request flow is:

~~~text
Frontend
  -> Student 2 backend/API
  -> shared RAG server
  -> relevant trusted context
  -> grounded local-LLM answer
  -> citations and confidence category
  -> Student 2 backend/API
  -> frontend
~~~

RAG Mode supports corpus refresh, context retrieval, grounded answers, citations, confidence categories, and explicit insufficient-context handling.

If relevant evidence cannot be found, the shared RAG service returns an insufficient-context result rather than generating an unsupported answer.

## AI Mode

The existing AI-assisted Skill Exchange workflow remains available.

Its Plan, Act, Observe, and Adapt flow identifies the requester and evidence, retrieves eligible candidates, invokes the configured local model, validates returned listing IDs against application evidence, and can retry with stricter constraints when validation fails.

AI recommendations remain advisory. The user can accept or reject a recommendation, and an exchange is not created automatically.

## CI/CD

Student 2 CI is defined in:

~~~text
.github/workflows/student-2-ci.yml
~~~

The workflow validates the Docker Compose configuration, builds the Student 2 images, starts the containerised services, performs readiness checks, runs smoke tests, runs CRUD and deterministic matching validation, and creates CI evidence.

The AI, MCP, and RAG integrations remain in the codebase but are explicitly disabled during CI:

~~~text
AI_ENABLED=false
MCP_ENABLED=false
RAG_ENABLED=false
~~~

The workflow verifies those values inside the running Student 2 backend container.

This allows Student 2 CI to run without depending on the local shared MCP and RAG processes.

## Release 1 Validation

Student 2 Release 1 has been locally validated for normal CRUD operations, search, deterministic candidate matching, AI-assisted matching, inactive and invalid listing handling, MCP skill search, MCP listing retrieval, RAG corpus refresh, RAG retrieval, grounded answers with citations and confidence, and insufficient-context handling.

Student 2 has also been regression tested against the combined Student 1, Student 2, and Student 3 shared RAG corpus.

## Evidence

Release-specific validation evidence should be referenced in the group technical report and contribution records.

The existing `evidence/agentic_loop_record_template.md` is retained as evidence relating to the existing Student 2 AI workflow. It should not be treated as evidence that the shared Release 1 agentic-loop service is complete.
