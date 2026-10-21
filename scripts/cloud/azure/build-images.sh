#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

IMAGE_TAG="${IMAGE_TAG:-release2}"

build_image() {
    local name="$1"
    local dockerfile="$2"
    local context="$3"

    local image="asd-group22-${name}:${IMAGE_TAG}"

    echo
    echo "============================================================"
    echo "Building ${image}"
    echo "Dockerfile: ${dockerfile}"
    echo "Context: ${context}"
    echo "============================================================"

    docker build \
        -f "$dockerfile" \
        -t "$image" \
        "$context"
}

echo "Group 22 Release 2 image build"
echo "Repository root: $ROOT_DIR"
echo "Image tag: $IMAGE_TAG"

# ------------------------------------------------------------
# Shared home
# ------------------------------------------------------------

build_image \
    "home" \
    "scripts/cloud/azure/dockerfiles/home.Dockerfile" \
    "."

# ------------------------------------------------------------
# Student 1 - Project Management
# ------------------------------------------------------------

build_image \
    "student1-database" \
    "student-1/database/Dockerfile" \
    "student-1/database"

build_image \
    "student1-backend" \
    "student-1/backend/Dockerfile" \
    "student-1/backend"

build_image \
    "student1-frontend" \
    "scripts/cloud/azure/dockerfiles/student1-frontend.Dockerfile" \
    "."

# ------------------------------------------------------------
# Student 2 - Skill Exchange
# ------------------------------------------------------------

build_image \
    "student2-database" \
    "student-2/database-service/Dockerfile" \
    "student-2/database-service"

build_image \
    "student2-backend" \
    "student-2/backend-service/Dockerfile" \
    "student-2"

build_image \
    "student2-frontend" \
    "scripts/cloud/azure/dockerfiles/student2-frontend.Dockerfile" \
    "."

# ------------------------------------------------------------
# Student 3 - Project Group Formation
# ------------------------------------------------------------

build_image \
    "student3-database" \
    "student-3/database-service/Dockerfile" \
    "student-3/database-service"

build_image \
    "student3-backend" \
    "scripts/cloud/azure/dockerfiles/student3-backend.Dockerfile" \
    "."

build_image \
    "student3-frontend" \
    "scripts/cloud/azure/dockerfiles/student3-frontend.Dockerfile" \
    "."

# ------------------------------------------------------------
# Student 4 - Skill Profile
# ------------------------------------------------------------

build_image \
    "student4-database" \
    "student-4/database/Dockerfile" \
    "student-4/database"

build_image \
    "student4-backend" \
    "student-4/backend/Dockerfile" \
    "student-4/backend"

build_image \
    "student4-frontend" \
    "student-4/frontend/Dockerfile" \
    "student-4/frontend"

# ------------------------------------------------------------
# Student 5 - AI Campus Space Finder
# ------------------------------------------------------------

build_image \
    "student5-database" \
    "student-5/database/Dockerfile" \
    "student-5/database"

build_image \
    "student5-backend" \
    "student-5/backend/Dockerfile" \
    "student-5/backend"

build_image \
    "student5-frontend" \
    "scripts/cloud/azure/dockerfiles/student5-frontend.Dockerfile" \
    "."

echo
echo "============================================================"
echo "All 16 Group 22 images built successfully."
echo "Image tag: $IMAGE_TAG"
echo "============================================================"
