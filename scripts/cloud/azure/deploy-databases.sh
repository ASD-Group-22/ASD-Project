#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-lab11-rg}"
ACA_ENV="${ACA_ENV:-lab11-env-31080-standard}"
ACR_NAME="${ACR_NAME:-lab11registry3098}"
IDENTITY_NAME="${IDENTITY_NAME:-g22-r2-acr-pull}"
IMAGE_TAG="${IMAGE_TAG:-release2}"

echo "============================================================"
echo "Group 22 Release 2 database deployment"
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

deploy_database() {
    local app_name="$1"
    local repository="$2"
    local target_port="$3"

    local image="${LOGIN_SERVER}/${repository}:${IMAGE_TAG}"

    echo
    echo "============================================================"
    echo "Database app: $app_name"
    echo "Image:        $image"
    echo "Target port:  $target_port"
    echo "============================================================"

    if az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --output none \
        2>/dev/null; then

        echo "Existing Container App found. Updating image and scale..."

        az containerapp update \
            --name "$app_name" \
            --resource-group "$RESOURCE_GROUP" \
            --image "$image" \
            --min-replicas 0 \
            --max-replicas 1 \
            --only-show-errors \
            --output none

        echo "Ensuring internal ingress configuration..."

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
            --min-replicas 0 \
            --max-replicas 1 \
            --only-show-errors \
            --output none
    fi

    fqdn="$(az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn \
        --output tsv)"

    echo "Ready: $app_name"
    echo "Internal FQDN: $fqdn"
}

deploy_database \
    "g22-r2-s1-db" \
    "student1-database" \
    "6001"

deploy_database \
    "g22-r2-s2-db" \
    "student2-database" \
    "5002"

deploy_database \
    "g22-r2-s3-db" \
    "student3-database" \
    "6000"

deploy_database \
    "g22-r2-s4-db" \
    "student4-database" \
    "5004"

deploy_database \
    "g22-r2-s5-db" \
    "student5-database" \
    "5000"

echo
echo "============================================================"
echo "All five Group 22 database apps deployed successfully."
echo "Scale: min 0 / max 1"
echo "Ingress: internal"
echo "============================================================"
