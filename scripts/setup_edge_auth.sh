#!/bin/bash
set -e

echo "==================================================="
echo "Setup Edge Authentication (Application Default)"
echo "==================================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    exit 1
fi

echo "Authenticating with Google Cloud..."
echo "This will open a browser or provide a link to authenticate."
echo "Ensure you log in with an account that has access to 'veiled-vector-core'."

gcloud auth application-default login

echo "==================================================="
echo "Authentication Complete!"
echo "Your Python scripts will now use these credentials automatically."
echo "==================================================="
