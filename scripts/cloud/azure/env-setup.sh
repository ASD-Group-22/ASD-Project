#!/usr/bin/env bash
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-lab11-rg}"
LOCATION="${LOCATION:-australiaeast}"
ACA_ENV="${ACA_ENV:-lab11-env-31080-standard}"
ACR_NAME="${ACR_NAME:-lab11registry3098}"
IDENTITY_NAME="${IDENTITY_NAME:-g22-r2-acr-pull}"

echo "============================================================"
echo "Group 22 Release 2 Azure setup"
echo "============================================================"
echo "Resource group: $RESOURCE_GROUP"
echo "Location:       $LOCATION"
echo "ACA environment:$ACA_ENV"
echo "ACR:            $ACR_NAME"
echo "Identity:       $IDENTITY_NAME"
echo

echo "Validating existing resource group..."
az group show \
    --name "$RESOURCE_GROUP" \
    --output none

echo "Validating existing Container Apps environment..."
az containerapp env show \
    --name "$ACA_ENV" \
    --resource-group "$RESOURCE_GROUP" \
    --output none

echo "Validating existing ACR..."
ACR_ID="$(az acr show \
    --name "$ACR_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query id \
    --output tsv)"

LOGIN_SERVER="$(az acr show \
    --name "$ACR_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query loginServer \
    --output tsv)"

if [[ -z "$ACR_ID" || -z "$LOGIN_SERVER" ]]; then
    echo "ERROR: Could not resolve ACR details." >&2
    exit 1
fi

echo "Existing Azure prerequisites: PASS"
echo

if az identity show \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --output none \
    2>/dev/null; then

    echo "Managed identity already exists: $IDENTITY_NAME"
else
    echo "Creating managed identity: $IDENTITY_NAME"

    az identity create \
        --name "$IDENTITY_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
fi

IDENTITY_ID="$(az identity show \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query id \
    --output tsv)"

PRINCIPAL_ID="$(az identity show \
    --name "$IDENTITY_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query principalId \
    --output tsv)"

if [[ -z "$IDENTITY_ID" || -z "$PRINCIPAL_ID" ]]; then
    echo "ERROR: Could not resolve managed identity." >&2
    exit 1
fi

echo
echo "Checking AcrPull assignment..."

ROLE_COUNT="$(MSYS_NO_PATHCONV=1 az role assignment list \
    --assignee-object-id "$PRINCIPAL_ID" \
    --scope "$ACR_ID" \
    --role "AcrPull" \
    --query "length(@)" \
    --output tsv)"

if [[ "$ROLE_COUNT" == "0" ]]; then
    echo "Assigning AcrPull..."

    MSYS_NO_PATHCONV=1 az role assignment create \
        --assignee-object-id "$PRINCIPAL_ID" \
        --assignee-principal-type ServicePrincipal \
        --role "AcrPull" \
        --scope "$ACR_ID" \
        --output none
else
    echo "AcrPull already assigned."
fi

echo
echo "============================================================"
echo "Azure setup ready."
echo "ACA environment: $ACA_ENV"
echo "Registry:        $LOGIN_SERVER"
echo "Identity ID:     $IDENTITY_ID"
echo "============================================================"
