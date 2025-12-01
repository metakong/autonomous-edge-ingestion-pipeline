import requests
import json
import os
import time

# We will use the REST API directly since the Admin SDK doesn't support Rules deployment easily.
# We need an access token. We can get this from gcloud if available, or we might need to rely on the user having `gcloud auth print-access-token` working.

PROJECT_ID = "veiled-vector-core"
RULES_FILE = "firestore.rules"

def get_access_token():
    try:
        # Try to get token from gcloud
        token = os.popen("gcloud auth print-access-token").read().strip()
        if token:
            return token
    except Exception as e:
        print(f"Failed to get token from gcloud: {e}")
    return None

def deploy_rules():
    token = get_access_token()
    if not token:
        print("Error: Could not obtain access token. Please run 'gcloud auth login' or ensure credentials are set.")
        return

    with open(RULES_FILE, 'r') as f:
        rules_content = f.read()

    url = f"https://firebaserules.googleapis.com/v1/projects/{PROJECT_ID}/rulesets"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": PROJECT_ID  # Force quota project
    }
    
    # 1. Create a Ruleset
    payload = {
        "source": {
            "files": [
                {
                    "content": rules_content,
                    "name": "firestore.rules"
                }
            ]
        }
    }
    
    print("Creating Ruleset...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error creating ruleset: {response.text}")
        return

    ruleset_name = response.json().get("name")
    print(f"Ruleset created: {ruleset_name}")

    # 2. Update the Release to point to this new Ruleset
    # The release name for Firestore is usually "cloud.firestore"
    release_name = f"projects/{PROJECT_ID}/releases/cloud.firestore"
    
    update_payload = {
        "rulesetName": ruleset_name
    }
    
    print(f"Updating Release {release_name}...")
    # We use PATCH to update the release
    response = requests.patch(f"https://firebaserules.googleapis.com/v1/{release_name}", headers=headers, json=update_payload)
    
    if response.status_code != 200:
        print(f"Error updating release: {response.text}")
        # If it doesn't exist, we might need to create it (POST)
        print("Attempting to create release instead...")
        create_payload = {
            "name": release_name,
            "rulesetName": ruleset_name
        }
        response = requests.post(f"https://firebaserules.googleapis.com/v1/projects/{PROJECT_ID}/releases", headers=headers, json=create_payload)
        if response.status_code != 200:
             print(f"Error creating release: {response.text}")
             return

    print("SUCCESS: Firestore Security Rules Deployed!")

if __name__ == "__main__":
    deploy_rules()
