#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-lab11-rg}"
ACA_ENV="${ACA_ENV:-lab11-env-31080-standard}"
ACR_NAME="${ACR_NAME:-lab11registry3098}"
IDENTITY_NAME="${IDENTITY_NAME:-g22-r2-acr-pull}"
IMAGE_TAG="${IMAGE_TAG:-release2}"

echo "============================================================"
echo "Group 22 Release 2 frontend deployment"
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

deploy_frontend() {
    local app_name="$1"
    local repository="$2"
    local target_port="$3"
    shift 3

    local image="${LOGIN_SERVER}/${repository}:${IMAGE_TAG}"

    echo
    echo "============================================================"
    echo "Frontend app: $app_name"
    echo "Image:        $image"
    echo "Target port:  $target_port"
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
            --type external \
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
            --ingress external \
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
    echo "External URL: https://${fqdn}"
}

# ------------------------------------------------------------
# Resolve internal backend FQDNs
# ------------------------------------------------------------

S1_API_FQDN="$(get_fqdn "g22-r2-s1-api")"
S2_API_FQDN="$(get_fqdn "g22-r2-s2-api")"
S3_API_FQDN="$(get_fqdn "g22-r2-s3-api")"
S4_API_FQDN="$(get_fqdn "g22-r2-s4-api")"
S5_API_FQDN="$(get_fqdn "g22-r2-s5-api")"

echo "Backend FQDN resolution: PASS"

# ------------------------------------------------------------
# Student 4 first - Student 3 needs its public frontend URL
# ------------------------------------------------------------

deploy_frontend \
    "g22-r2-s4-web" \
    "student4-frontend" \
    "5006" \
    "BACKEND_SERVICE_URL=https://${S4_API_FQDN}"

S4_WEB_FQDN="$(get_fqdn "g22-r2-s4-web")"

if [[ -z "$S4_WEB_FQDN" ]]; then
    echo "ERROR: Student 4 frontend FQDN could not be resolved." >&2
    exit 1
fi

# ------------------------------------------------------------
# Student 1
# ------------------------------------------------------------

deploy_frontend \
    "g22-r2-s1-web" \
    "student1-frontend" \
    "80" \
    "BACKEND_ORIGIN=https://${S1_API_FQDN}"

# ------------------------------------------------------------
# Student 2
# ------------------------------------------------------------

deploy_frontend \
    "g22-r2-s2-web" \
    "student2-frontend" \
    "80" \
    "BACKEND_ORIGIN=https://${S2_API_FQDN}"

# ------------------------------------------------------------
# Student 3
# ------------------------------------------------------------

deploy_frontend \
    "g22-r2-s3-web" \
    "student3-frontend" \
    "80" \
    "BACKEND_ORIGIN=https://${S3_API_FQDN}" \
    "STUDENT4_FRONTEND_URL=https://${S4_WEB_FQDN}"

# ------------------------------------------------------------
# Student 5
# ------------------------------------------------------------

deploy_frontend \
    "g22-r2-s5-web" \
    "student5-frontend" \
    "8005" \
    "BACKEND_ORIGIN=https://${S5_API_FQDN}"

echo
echo "============================================================"
echo "All five Group 22 frontend apps deployed successfully."
echo "Scale: min 0 / max 1"
echo "Ingress: external"
echo "============================================================"
