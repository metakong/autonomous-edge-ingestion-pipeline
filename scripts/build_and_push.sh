#!/bin/bash
set -e

PROJECT_ID="veiled-vector-core"
REGION="us-central1"
REPO_NAME="veiled-vector-repo"
IMAGE_NAME="core"
TAG="latest"

echo "--- Starting Build & Push for $PROJECT_ID ---"

# 1. Enable Artifact Registry API
echo "Enabling Artifact Registry API..."
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID

# 2. Create Repository (if not exists)
echo "Checking/Creating Repository..."
if ! gcloud artifacts repositories describe $REPO_NAME --project=$PROJECT_ID --location=$REGION > /dev/null 2>&1; then
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="Veiled Vector Core Docker Repository" \
        --project=$PROJECT_ID
    echo "Repository $REPO_NAME created."
else
    echo "Repository $REPO_NAME already exists."
fi

# 3. Configure Docker Auth
echo "Configuring Docker Auth..."
gcloud auth configure-docker $REGION-docker.pkg.dev --quiet

# 4. Build Image
FULL_IMAGE_PATH="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG"
echo "Building Docker Image: $FULL_IMAGE_PATH"
docker build -t $FULL_IMAGE_PATH .

# 5. Push Image
echo "Pushing Image to Artifact Registry..."
docker push $FULL_IMAGE_PATH

echo "--- Build & Push Complete! ---"
echo "Image available at: $FULL_IMAGE_PATH"
