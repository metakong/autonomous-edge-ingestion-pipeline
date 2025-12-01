#!/bin/bash
set -e

# Configuration
PROJECT_ID="veiled-vector-core"
SERVICE_NAME="veiled-vector-dashboard"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "==================================================="
echo "Deploying Dashboard to Cloud Run (via Cloud Build)"
echo "==================================================="

# Navigate to dashboard directory
cd "$(dirname "$0")/../dashboard"

# Submit build to Cloud Build
echo "[1/2] Submitting build to Google Cloud Build..."
gcloud builds submit --tag "$IMAGE_NAME" .

# Deploy to Cloud Run
echo "[2/2] Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 3000

echo "==================================================="
echo "Deployment Complete!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')"
echo "==================================================="
