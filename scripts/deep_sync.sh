#!/bin/bash

PROJECT_ID="veiled-vector-core"

echo "=== SECRET MANAGER SECRETS ==="
gcloud secrets list --project="$PROJECT_ID" --format="table(name,createTime)"

echo -e "\n=== FIRESTORE DATABASES ==="
gcloud firestore databases list --project="$PROJECT_ID" --format="table(name,locationId,type)"

echo -e "\n=== IAM SERVICE ACCOUNTS ==="
gcloud iam service-accounts list --project="$PROJECT_ID" --format="table(email,displayName,disabled)"

echo -e "\n=== ENABLED APIS (Top 20) ==="
gcloud services list --enabled --project="$PROJECT_ID" --limit=20 --format="table(config.name,config.title)"

echo -e "\n=== VPC CONNECTORS (Network) ==="
gcloud compute networks vpc-access connectors list --region=us-central1 --project="$PROJECT_ID" --format="table(name,network,state)" || echo "No connectors found or API disabled"
