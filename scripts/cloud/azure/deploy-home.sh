#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-lab11-rg}"
ACA_ENV="${ACA_ENV:-lab11-env-31080-standard}"
ACR_NAME="${ACR_NAME:-lab11registry3098}"
IDENTITY_NAME="${IDENTITY_NAME:-g22-r2-acr-pull}"
IMAGE_TAG="${IMAGE_TAG:-release2}"

APP_NAME="${APP_NAME:-g22-r2-home}"
REPOSITORY="${REPOSITORY:-home}"

echo "============================================================"
echo "Group 22 Release 2 shared home deployment"
echo "============================================================"
echo "Resource group: $RESOURCE_GROUP"
echo "Environment:    $ACA_ENV"
echo "ACR:            $ACR_NAME"
echo "Image tag:      $IMAGE_TAG"
echo "App:            $APP_NAME"
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

get_fqdn() {
    local app_name="$1"

    az containerapp show \
        --name "$app_name" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn \
        --output tsv
}

S1_WEB_FQDN="$(get_fqdn "g22-r2-s1-web")"
S2_WEB_FQDN="$(get_fqdn "g22-r2-s2-web")"
S3_WEB_FQDN="$(get_fqdn "g22-r2-s3-web")"
S4_WEB_FQDN="$(get_fqdn "g22-r2-s4-web")"
S5_WEB_FQDN="$(get_fqdn "g22-r2-s5-web")"

if [[ -z "$S1_WEB_FQDN" || \
      -z "$S2_WEB_FQDN" || \
      -z "$S3_WEB_FQDN" || \
      -z "$S4_WEB_FQDN" || \
      -z "$S5_WEB_FQDN" ]]; then
    echo "ERROR: Could not resolve all five frontend FQDNs." >&2
    exit 1
fi

echo "Frontend FQDN resolution: PASS"

IMAGE="${LOGIN_SERVER}/${REPOSITORY}:${IMAGE_TAG}"

if az containerapp show \
    --name "$APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --output none \
    2>/dev/null; then

    echo "Existing shared home found. Updating..."

    az containerapp update \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --image "$IMAGE" \
        --set-env-vars \
            "STUDENT1_FRONTEND_URL=https://${S1_WEB_FQDN}" \
            "STUDENT2_FRONTEND_URL=https://${S2_WEB_FQDN}" \
            "STUDENT3_FRONTEND_URL=https://${S3_WEB_FQDN}" \
            "STUDENT4_FRONTEND_URL=https://${S4_WEB_FQDN}" \
            "STUDENT5_FRONTEND_URL=https://${S5_WEB_FQDN}" \
        --min-replicas 0 \
        --max-replicas 1 \
        --only-show-errors \
        --output none

    az containerapp ingress enable \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --type external \
        --target-port 80 \
        --transport auto \
        --only-show-errors \
        --output none
else
    echo "Creating shared home Container App..."

    MSYS_NO_PATHCONV=1 az containerapp create \
        --name "$APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$ACA_ENV" \
        --image "$IMAGE" \
        --user-assigned "$IDENTITY_ID" \
        --registry-server "$LOGIN_SERVER" \
        --registry-identity "$IDENTITY_ID" \
        --ingress external \
        --target-port 80 \
        --transport auto \
        --env-vars \
            "STUDENT1_FRONTEND_URL=https://${S1_WEB_FQDN}" \
            "STUDENT2_FRONTEND_URL=https://${S2_WEB_FQDN}" \
            "STUDENT3_FRONTEND_URL=https://${S3_WEB_FQDN}" \
            "STUDENT4_FRONTEND_URL=https://${S4_WEB_FQDN}" \
            "STUDENT5_FRONTEND_URL=https://${S5_WEB_FQDN}" \
        --min-replicas 0 \
        --max-replicas 1 \
        --only-show-errors \
        --output none
fi

HOME_FQDN="$(get_fqdn "$APP_NAME")"

if [[ -z "$HOME_FQDN" ]]; then
    echo "ERROR: Shared home FQDN could not be resolved." >&2
    exit 1
fi

echo
echo "============================================================"
echo "Shared home deployed successfully."
echo "URL: https://${HOME_FQDN}"
echo "Scale: min 0 / max 1"
echo "Ingress: external"
echo "============================================================"
