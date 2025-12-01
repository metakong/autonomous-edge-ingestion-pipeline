#!/bin/bash
echo "=== CLOUD RUN SERVICES ==="
gcloud run services list --project=veiled-vector-core --format="table(name,status.url,status.latestCreatedRevisionName)"

echo -e "\n=== CLOUD RUN JOBS ==="
gcloud run jobs list --project=veiled-vector-core --format="table(name,status.latestCreatedExecution.createTime)"

echo -e "\n=== CLOUD STORAGE BUCKETS ==="
gcloud storage buckets list --project=veiled-vector-core --format="table(name,location,storageClass)"

echo -e "\n=== CLOUD SCHEDULER JOBS ==="
gcloud scheduler jobs list --project=veiled-vector-core --location=us-central1 --format="table(name,schedule,state,target)"

echo -e "\n=== PUBSUB TOPICS ==="
gcloud pubsub topics list --project=veiled-vector-core --format="table(name)"

echo -e "\n=== FIRESTORE (via gcloud alpha) ==="
# Attempting to list indexes as a proxy for activity, or just basic info
gcloud alpha firestore indexes composite list --project=veiled-vector-core --format="table(collectionGroup)" || echo "Could not list indexes"
