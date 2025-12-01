#!/bin/bash
set -e

PROJECT_ID="veiled-vector-core"
REGION="us-central1"
JOB_NAME="veiled-vector-orchestrator-job"
IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/veiled-vector-repo/core:latest"
SERVICE_ACCOUNT="813376341042-compute@developer.gserviceaccount.com"

echo "--- Deploying Cloud Run Job: $JOB_NAME ---"

gcloud run jobs deploy $JOB_NAME \
    --image $IMAGE \
    --region $REGION \
    --project $PROJECT_ID \
    --service-account $SERVICE_ACCOUNT \
    --memory 2Gi \
    --cpu 1 \
    --task-timeout 3600s \
    --command python \
    --args src/orchestrator.py,--run-once \
    --set-env-vars PROJECT_ID=$PROJECT_ID,GOOGLE_CLOUD_PROJECT=$PROJECT_ID

echo "--- Deployment Complete ---"
echo "To execute the job manually: gcloud run jobs execute $JOB_NAME --region $REGION"
