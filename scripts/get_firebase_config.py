import requests
import google.auth
from google.auth.transport.requests import Request

def get_firebase_config(project_id):
    scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/firebase"]
    credentials, project = google.auth.default(scopes=scopes)
    credentials.refresh(Request())
    token = credentials.token

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. List Web Apps
    url = f"https://firebase.googleapis.com/v1beta1/projects/{project_id}/webApps"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        print("Firebase not enabled on project. Adding Firebase...")
        add_url = f"https://firebase.googleapis.com/v1beta1/projects/{project_id}:addFirebase"
        add_resp = requests.post(add_url, headers=headers, json={})
        if add_resp.status_code != 200 and add_resp.status_code != 202:
            print(f"Error adding Firebase: {add_resp.text}")
            return
        print("Firebase added. Waiting a moment...")
        import time
        time.sleep(10)
        # Retry list
        response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error listing apps: {response.text}")
        return

    apps = response.json().get("apps", [])
    if not apps:
        print("No Web Apps found. Creating one...")
        # Create App
        create_url = f"https://firebase.googleapis.com/v1beta1/projects/{project_id}/webApps"
        data = {"displayName": "CEO Dashboard"}
        create_resp = requests.post(create_url, headers=headers, json=data)
        if create_resp.status_code != 200:
            print(f"Error creating app: {create_resp.text}")
            return
        # Wait for operation? It returns an operation.
        # Usually creation is fast enough or we get the appId in the operation metadata?
        # Actually, let's just list again or parse the operation.
        # For simplicity, let's assume we need to wait or just use the one we found if any.
        # If we just created it, we might need to query the operation result.
        print("App creation initiated. Please run this script again in a few seconds.")
        return

    app_id = apps[0]["appId"]
    print(f"Found App ID: {app_id}")

    # 2. Get Config
    config_url = f"https://firebase.googleapis.com/v1beta1/projects/{project_id}/webApps/{app_id}/config"
    config_resp = requests.get(config_url, headers=headers)
    
    if config_resp.status_code == 200:
        print("Firebase Config:")
        print(config_resp.json())
    else:
        print(f"Error getting config: {config_resp.text}")

if __name__ == "__main__":
    get_firebase_config("veiled-vector-core")
