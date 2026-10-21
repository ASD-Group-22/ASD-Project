# Release 2 Cloud Deployment Report

## Deployment Summary

The Release 2 integrated University Management Platform was successfully deployed to Microsoft Azure from the official Group 22 repository.

- Repository: `ASD-Group-22/ASD-Project`
- Branch: `release2/cloud-deployment`
- Commit: `f18c9175457e54423db1214b37e9a57e433c63fa`
- GitHub Actions run: `39589826282`
- Image tag: `release2-f18c917`
- Resource group: `lab11-rg`
- Container Apps environment: `lab11-env-31080-standard`
- Azure Container Registry: `lab11registry3098`
- Deployment result: **PASS**

## Architecture

The cloud deployment contains 16 Group 22 Release 2 Azure Container Apps:

- 1 shared home application
- 5 student frontend applications
- 5 student backend/API applications
- 5 student database applications

The shared home and the five student frontend applications use external ingress.

Student backend and database Container Apps use internal ingress so they are not exposed directly to the public internet.

Frontend applications communicate with their corresponding backend services through cloud-compatible proxy routing. Backends communicate with database services using their internal Azure Container Apps FQDNs.

Student 2 and Student 3 also communicate with the Student 4 Skill Profile backend using its internal Azure FQDN.

## Release 2 Cloud Baseline

The local Release 2 AI services are intentionally disabled in the cloud baseline.

Student 1:
- `AI_ENABLED=false`
- `MCP_ENABLED=false`
- `RAG_ENABLED=false`

Student 2:
- `AI_ENABLED=false`
- `ENABLE_REVIEW_MODEL=false`
- `MCP_ENABLED=false`
- `RAG_ENABLED=false`
- `MULTI_AGENT_ENABLED=false`

Student 3:
- `AI_ENABLED=false`
- `MCP_ENABLED=false`
- `RAG_ENABLED=false`

Student 4:
- `AI_ENABLED=false`
- `MCP_ENABLED=false`
- `RAG_ENABLED=false`
- `FLASK_DEBUG=false`

Student 5:
- `AI_MODE=false`
- `MCP_MODE=false`
- `RAG_MODE=false`

MCP, RAG, Multi-Agent and the local agentic services are therefore not required as Azure Container Apps for the baseline cloud deployment.

## CI and Security Validation

The deployment workflow required successful Student 1 through Student 5 CI runs for the exact deployment commit before Azure deployment could begin.

For commit `f18c9175457e54423db1214b37e9a57e433c63fa`:

- Student 1 CI: PASS
- Student 2 CI: PASS
- Student 3 CI: PASS
- Student 4 CI: PASS
- Student 5 CI: PASS
- Release 2 integration CI: PASS

Before the cloud implementation was committed, the repository security checks also passed:

- Ruff security and correctness: PASS
- detect-secrets: PASS
- pip-audit Release 2 dependencies: PASS

Student 4 dependency versions were updated to remove vulnerabilities identified by pip-audit.

## Azure Authentication

GitHub Actions authenticates to Azure using OpenID Connect rather than a stored Azure client secret.

The official Group 22 repository and `release2/cloud-deployment` branch were added as a federated credential on the existing `g22-r2-github-oidc` managed identity.

The deployment identity has Contributor access to the existing Release 2 Azure resource group.

The deployed Container Apps use the existing `g22-r2-acr-pull` managed identity for Azure Container Registry access.

## Deployment Validation

The official deployment workflow successfully:

1. validated the five required student CI workflows,
2. authenticated to Azure using GitHub OIDC,
3. verified the existing Azure resource group, registry, Container Apps environment and managed identity,
4. built all 16 Release 2 container images,
5. pushed the images to Azure Container Registry,
6. deployed five database Container Apps,
7. deployed five backend Container Apps,
8. deployed five frontend Container Apps,
9. deployed the shared home Container App,
10. executed integrated Azure deployment and CRUD validation.

The validation confirmed:

- all 16 Group 22 Release 2 Container Apps were provisioned successfully,
- the shared home returned HTML,
- the shared home linked to all five Azure student frontends,
- Student 1 CRUD passed,
- Student 2 CRUD passed, including soft-delete validation,
- Student 3 CRUD passed,
- Student 4 CRUD passed,
- Student 5 CRUD passed.

All feature validation requests were made through the externally exposed frontend applications while backend and database applications remained internal.

## Shared Home

The deployed shared home application is:

`https://g22-r2-home.gentlemushroom-26567496.australiaeast.azurecontainerapps.io`

## Limitations

Azure Container Apps scale-to-zero may cause a cold-start delay. The deployment validation includes retry behaviour for this condition.

The current Release 2 cloud baseline focuses on the integrated feature application with AI, MCP, RAG and Multi-Agent functionality disabled as required for the cloud baseline.

The deployment reuses the existing Azure infrastructure rather than creating a duplicate resource group, Container Apps environment or registry.

## Evidence

The detailed deployment evidence is stored in:

`reports/release2/cloud-deployment-results.md`

Official GitHub Actions deployment:

`https://github.com/ASD-Group-22/ASD-Project/actions/runs/39589826282`
