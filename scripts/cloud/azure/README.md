# Group 22 Azure Container Apps Deployment Blueprint

## Status

This directory contains the group-wide Azure Container Apps deployment
implementation used for the integrated Release 2 application.

It supports the shared home and all five student features using separate
frontend, backend and database Container Apps.

The deployment is orchestrated by `.github/workflows/cloud-deployment.yml` and
has been validated through the official Group 22 cloud workflow.

No group-wide Azure resources should be created merely by using the files in
this directory.

## Local vs Cloud Deployment

Local Release 2 continues to use the root:

    docker-compose.yml

The local integrated application contains 16 application containers:

- 1 shared home page
- 5 student frontends
- 5 student backends
- 5 student databases

The shared non-containerised local AI services remain local-only for the
required Release 2 cloud baseline:

- Ollama / AI runtime
- MCP server
- RAG server
- Multi-Agent server
- Agentic loop

The final cloud deployment is performed through Azure Container Apps rather
than docker-compose.cloud.yml.

## Target Azure Topology

All 16 application services are deployed into one Azure Container Apps
environment.

Ingress model:

- Shared home: external
- Student frontends: external
- Student backends: internal
- Student databases: internal

Browser traffic should never require direct access to an internal backend or
database.

Frontend applications should communicate with their own backend using either:

1. a same-origin reverse proxy such as /api, or
2. server-side requests from the frontend application container.

## Deployment Order

The planned deployment order is:

1. Azure resource group / Container Apps environment / ACR identity
2. Five database services
3. Student 4 backend
4. Remaining student backends
5. Five student frontends
6. Shared home page
7. Integrated cloud validation

Student 4 backend is deployed before Students 2 and 3 because both features
depend on the Skill Profile API.

## Cloud Baseline

Release 2 cloud feature services are disabled by default.

The exact environment-variable names differ between student implementations.

Student 1:
- MCP_ENABLED=false
- RAG_ENABLED=false
- AI_ENABLED=false

Student 2:
- AI_ENABLED=false
- ENABLE_REVIEW_MODEL=false
- MCP_ENABLED=false
- RAG_ENABLED=false
- MULTI_AGENT_ENABLED=false

Student 3:
- AI_ENABLED=false
- MCP_ENABLED=false
- RAG_ENABLED=false

Student 4:
- MCP_ENABLED=false
- RAG_ENABLED=false
- FLASK_DEBUG=false
- AI_ENABLED=false

Student 5:
- AI_MODE=false
- MCP_MODE=false
- RAG_MODE=false

The final deployment must verify the effective disabled state rather than
assuming all students use the same feature-flag names.

## Cross-Feature Dependencies

Student 2 backend:
- Student 2 database
- Student 4 Skill Profile backend

Student 3 backend:
- Student 3 database
- Student 4 Skill Profile backend

The Student 4 backend ACA internal FQDN therefore needs to be supplied to both
Student 2 and Student 3 through SKILL_PROFILE_SERVICE_URL.

## Container Image Workflow

The Azure for Students deployment does not rely on ACR Tasks. The validated
workflow uses:

    docker build
        -> az acr login
        -> docker tag
        -> docker push
        -> Azure Container Apps deployment/update

The group deployment scripts are:

    env-setup.sh
    build-images.sh
    push-images.sh
    deploy-databases.sh
    deploy-backends.sh
    deploy-frontends.sh
    deploy-home.sh
    deployment-testing.ps1

These scripts are orchestrated by the official cloud deployment workflow.

## Persistence

The integrated deployment uses the existing SQLite database services. The
Azure Container Apps writable filesystem is ephemeral, so this configuration
is suitable for the current assessment demonstration but is not production-grade
persistent storage.

A production deployment would require a persistent storage design, such as
Azure Files or a managed database service.

## GitHub Actions

The `.github/workflows/cloud-deployment.yml` workflow acts as a thin
orchestrator.

It:

1. run only after required validation succeeds,
2. authenticate to Azure using the approved GitHub/Azure mechanism,
3. build and push images,
4. invoke the reusable deployment scripts,
5. run integrated deployment validation,
6. retain useful deployment evidence.

The workflow must not claim successful integrated deployment until all five
features and the shared home have actually been deployed and validated.
