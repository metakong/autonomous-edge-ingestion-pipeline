import subprocess
import json
import sys
from datetime import datetime

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return None

def get_cloud_run_services():
    print("  - Fetching Cloud Run services...")
    raw = run_command("gcloud run services list --format=json --project=veiled-vector-core")
    if not raw:
        return []
    return json.loads(raw)

def main():
    print(f"# Status Report: {datetime.now().isoformat()}")
    print("## Cloud Run Services")
    
    services = get_cloud_run_services()
    if not services:
        print("  - No active services found or error fetching.")
    else:
        for s in services:
            name = s.get('metadata', {}).get('name', 'Unknown')
            status = s.get('status', {}).get('conditions', [{}])[0].get('status', 'Unknown')
            url = s.get('status', {}).get('url', 'N/A')
            print(f"  - **{name}**: {status} ({url})")

    print("\n## Firestore Mission Queue")
    # Note: Using gcloud alpha firestore indexes is complex, so we'll just check if we can list collections
    # A full firestore check requires the python client library which might not be authenticated in all envs
    # so we stick to gcloud for reliability in this script.
    print("  - (Firestore check requires Python client - skipping for lightweight script)")

if __name__ == "__main__":
    main()
