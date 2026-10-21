# Group 22 Azure Service Map

This map reflects the integrated Release 2 service architecture defined by the
current root `docker-compose.yml`.

| Service | Container Port | ACA Ingress | Main Dependencies |
|---|---:|---|---|
| home-page | 80 | External | Five student frontends |
| student-1-database-service | 6001 | Internal | - |
| student-1-backend-service | 5001 | Internal | Student 1 database |
| student-1-frontend-service | 80 | External | Student 1 backend |
| student-2-skill-exchange-database | 5002 | Internal | - |
| student-2-skill-exchange-backend | 5001 | Internal | Student 2 database, Student 4 backend |
| student-2-skill-exchange-frontend | 80 | External | Student 2 backend |
| student-3-database | 6000 | Internal | - |
| student-3-backend | 5000 | Internal | Student 3 database, Student 4 backend |
| student-3-frontend | 8000 | External | Student 3 backend |
| student-4-database | 5004 | Internal | - |
| student-4-backend | 5005 | Internal | Student 4 database |
| student-4-frontend | 5006 | External | Student 4 backend |
| student-5-database | 5000 | Internal | - |
| student-5-backend | 8055 | Internal | Student 5 database |
| student-5-frontend | 8005 | External | Student 5 backend |

## Backend Database Configuration

Student 1:

    DATABASE_SERVICE_URL=https://<student-1-database-fqdn>

Student 2:

    DATABASE_SERVICE_URL=https://<student-2-database-fqdn>
    SKILL_PROFILE_SERVICE_URL=https://<student-4-backend-fqdn>

Student 3:

    DB_URL=https://<student-3-database-fqdn>
    SKILL_PROFILE_SERVICE_URL=https://<student-4-backend-fqdn>

Student 4:

    DATABASE_SERVICE_URL=https://<student-4-database-fqdn>

Student 5:

    DATABASE_SERVICE_URL=https://<student-5-database-fqdn>

Actual FQDNs must be resolved after the corresponding Container App has been
created. No localhost, Docker service names or host.docker.internal addresses
should be used for application-to-application cloud communication.

## Additional Build Requirement

Student 3 currently mounts its prompts directory through Docker Compose.

Container Apps cannot use that local repository bind mount.

The final Student 3 cloud image therefore needs the required prompt files
copied into the image during the Docker build.
