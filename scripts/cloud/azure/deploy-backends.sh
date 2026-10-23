#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-lab11-rg}"
ACA_ENV="${ACA_ENV:-lab11-env-31080-standard}"
ACR_NAME="${ACR_NAME:-lab11registry3098}"
IDENTITY_NAME="${IDENTITY_NAME:-g22-r2-acr-pull}"
IMAGE_TAG="${IMAGE_TAG:-release2}"

echo "============================================================"
echo "Group 22 Release 2 backend deployment"
echo "============================================================"
echo "Resource group: $RESOURCE_GROUP"
echo "Environment:    $ACA_ENV"
echo "ACR:            $ACR_NAME"
echo "Image tag:      $IMAGE_TAG"
echo

LOGIN_SERVER="$(az acr show \
    --name "$ACR_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query loginServer \
    --output tsv)"

IDENTITY_ID="$(az identity show \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query id \
    --output tsv)"

if [[ -z "$LOGIN_SERVER" || -z "$IDENTITY_ID" ]]; then
    echo "ERROR: Could not resolve ACR or managed identity." >&2
    exit 1
fi

az containerapp env show \
    --name "$ACA_ENV" \
    --resource-group "$RESOURCE_GROUP" \
    --output none

get_fqdn() {
    local app_name="$1"

    az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn \
        --output tsv
}

deploy_backend() {
    local app_name="$1"
    local repository="$2"
    local target_port="$3"
    shift 3

    local image="${LOGIN_SERVER}/${repository}:${IMAGE_TAG}"

    echo
    echo "============================================================"
    echo "Backend app: $app_name"
    echo "Image:       $image"
    echo "Target port: $target_port"
    echo "============================================================"

    if az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --output none \
        2>/dev/null; then

        echo "Existing Container App found. Updating..."

        az containerapp update \
            --name "$app_name" \
            --resource-group "$RESOURCE_GROUP" \
            --image "$image" \
            --set-env-vars "$@" \
            --min-replicas 0 \
            --max-replicas 1 \
            --only-show-errors \
            --output none

        az containerapp ingress enable \
            --name "$app_name" \
            --resource-group "$RESOURCE_GROUP" \
            --type internal \
            --target-port "$target_port" \
            --transport auto \
            --only-show-errors \
            --output none
    else
        echo "Creating Container App..."

        MSYS_NO_PATHCONV=1 az containerapp create \
            --name "$app_name" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "$ACA_ENV" \
            --image "$image" \
            --user-assigned "$IDENTITY_ID" \
            --registry-server "$LOGIN_SERVER" \
            --registry-identity "$IDENTITY_ID" \
            --ingress internal \
            --target-port "$target_port" \
            --transport auto \
            --env-vars "$@" \
            --min-replicas 0 \
            --max-replicas 1 \
            --only-show-errors \
            --output none
    fi

    local fqdn
    fqdn="$(get_fqdn "$app_name")"

    echo "Ready: $app_name"
    echo "Internal FQDN: $fqdn"
}

# ------------------------------------------------------------
# Resolve database service URLs
# ------------------------------------------------------------

S1_DB_FQDN="$(get_fqdn "g22-r2-s1-db")"
S2_DB_FQDN="$(get_fqdn "g22-r2-s2-db")"
S3_DB_FQDN="$(get_fqdn "g22-r2-s3-db")"
S4_DB_FQDN="$(get_fqdn "g22-r2-s4-db")"
S5_DB_FQDN="$(get_fqdn "g22-r2-s5-db")"

echo "Database FQDN resolution: PASS"

# ------------------------------------------------------------
# Student 4 first - S2 and S3 depend on Skill Profile
# ------------------------------------------------------------

deploy_backend \
    "g22-r2-s4-api" \
    "student4-backend" \
    "5005" \
    "DATABASE_SERVICE_URL=https://${S4_DB_FQDN}" \
    "AI_ENABLED=false" \
    "MCP_ENABLED=false" \
    "RAG_ENABLED=false" \
    "MULTI_AGENT_ENABLED=false" \
    "FLASK_DEBUG=false"

S4_API_FQDN="$(get_fqdn "g22-r2-s4-api")"

if [[ -z "$S4_API_FQDN" ]]; then
    echo "ERROR: Student 4 backend FQDN could not be resolved." >&2
    exit 1
fi

echo
echo "Student 4 dependency available:"
echo "https://${S4_API_FQDN}"

# ------------------------------------------------------------
# Student 1 - Project Management
# ------------------------------------------------------------

deploy_backend \
    "g22-r2-s1-api" \
    "student1-backend" \
    "5001" \
    "DATABASE_SERVICE_URL=https://${S1_DB_FQDN}" \
    "AI_ENABLED=false" \
    "MCP_ENABLED=false" \
    "RAG_ENABLED=false" \
    "MULTI_AGENT_ENABLED=false"

# ------------------------------------------------------------
# Student 2 - Skill Exchange
# ------------------------------------------------------------

deploy_backend \
    "g22-r2-s2-api" \
    "student2-backend" \
    "5001" \
    "DATABASE_SERVICE_URL=https://${S2_DB_FQDN}" \
    "SKILL_PROFILE_SERVICE_URL=https://${S4_API_FQDN}" \
    "AI_ENABLED=false" \
    "ENABLE_REVIEW_MODEL=false" \
    "MCP_ENABLED=false" \
    "RAG_ENABLED=false" \
    "MULTI_AGENT_ENABLED=false"

# ------------------------------------------------------------
# Student 3 - Project Group Formation
# ------------------------------------------------------------

deploy_backend \
    "g22-r2-s3-api" \
    "student3-backend" \
    "5000" \
    "DB_URL=https://${S3_DB_FQDN}" \
    "SKILL_PROFILE_SERVICE_URL=https://${S4_API_FQDN}" \
    "PROMPT_ROOT=/prompts" \
    "AI_ENABLED=false" \
    "MCP_ENABLED=false" \
    "RAG_ENABLED=false" \
    "MULTI_AGENT_ENABLED=false"

# ------------------------------------------------------------
# Student 5 - AI Campus Space Finder
# ------------------------------------------------------------

deploy_backend \
    "g22-r2-s5-api" \
    "student5-backend" \
    "8055" \
    "DATABASE_SERVICE_URL=https://${S5_DB_FQDN}" \
    "AI_MODE=false" \
    "MCP_MODE=false" \
    "RAG_MODE=false" \
    "MULTI_AGENT_MODE=false"

echo
echo "============================================================"
echo "All five Group 22 backend apps deployed successfully."
echo "AI / MCP / RAG / Multi-Agent cloud baseline: disabled"
echo "Scale: min 0 / max 1"
echo "Ingress: internal"
echo "============================================================"
