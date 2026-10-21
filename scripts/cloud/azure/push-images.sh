#!/usr/bin/env bash
set -euo pipefail

ACR_NAME="${ACR_NAME:-}"
IMAGE_TAG="${IMAGE_TAG:-release2}"
REMOTE_TAG="${REMOTE_TAG:-$IMAGE_TAG}"

if [[ -z "$ACR_NAME" ]]; then
    echo "ERROR: ACR_NAME is required." >&2
    echo "Example: ACR_NAME=lab11registry3098 IMAGE_TAG=release2-local REMOTE_TAG=release2 ./scripts/cloud/azure/push-images.sh" >&2
    exit 1
fi

if ! command -v az >/dev/null 2>&1; then
    echo "ERROR: Azure CLI (az) is not available." >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not available." >&2
    exit 1
fi

LOGIN_SERVER="$(az acr show \
    --name "$ACR_NAME" \
    --query loginServer \
    --output tsv)"

if [[ -z "$LOGIN_SERVER" ]]; then
    echo "ERROR: Could not determine login server for ACR '$ACR_NAME'." >&2
    exit 1
fi

images=(
    "home"

    "student1-database"
    "student1-backend"
    "student1-frontend"

    "student2-database"
    "student2-backend"
    "student2-frontend"

    "student3-database"
    "student3-backend"
    "student3-frontend"

    "student4-database"
    "student4-backend"
    "student4-frontend"

    "student5-database"
    "student5-backend"
    "student5-frontend"
)

echo "Group 22 Release 2 image push"
echo "Registry: $LOGIN_SERVER"
echo "Local tag: $IMAGE_TAG"
echo "Remote tag: $REMOTE_TAG"

echo
echo "Checking all 16 local images before ACR login..."

for name in "${images[@]}"; do
    local_image="asd-group22-${name}:${IMAGE_TAG}"

    if ! docker image inspect "$local_image" >/dev/null 2>&1; then
        echo "ERROR: Required local image is missing: $local_image" >&2
        exit 1
    fi
done

echo "Local image check: PASS"

echo
echo "Logging into Azure Container Registry..."
az acr login --name "$ACR_NAME"

for name in "${images[@]}"; do
    local_image="asd-group22-${name}:${IMAGE_TAG}"
    remote_image="${LOGIN_SERVER}/${name}:${REMOTE_TAG}"

    echo
    echo "============================================================"
    echo "Pushing ${remote_image}"
    echo "============================================================"

    docker tag "$local_image" "$remote_image"
    docker push "$remote_image"
done

echo
echo "============================================================"
echo "All 16 Group 22 images pushed successfully."
echo "Registry: $LOGIN_SERVER"
echo "Tag: $REMOTE_TAG"
echo "============================================================"
