import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os

# Use implicit credentials (will work on Kaji if gcloud auth is set up, or we might need to point to a key)
# The user mentioned credentials.json is in the root, let's try to use it if it exists, otherwise default.

PROJECT_ID = "veiled-vector-core"
DB_NAME = "veiled-vector-core-firestore"

try:
    if os.path.exists("credentials.json"):
        cred = credentials.Certificate("credentials.json")
        firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
    else:
        firebase_admin.initialize_app(options={'projectId': PROJECT_ID})

    # db = firestore.client(database=DB_NAME) 
    # The above line failed. Let's try the direct Client constructor which supports 'database' in newer libs, 
    # or just default if that fails. For now, let's try to be explicit but safe.
    from google.cloud import firestore as google_firestore
    db = google_firestore.Client(project=PROJECT_ID, database=DB_NAME)

    print(f"Checking mission_queue in {DB_NAME}...")
    # docs = db.collection("mission_queue").where("status", "==", "PENDING").stream()
    docs = db.collection("mission_queue").order_by("created_at", direction=google_firestore.Query.DESCENDING).limit(5).stream()
    
    count = 0
    for doc in docs:
        data = doc.to_dict()
        print(f"FULL DATA for {doc.id}: {data}")
        print(f"Found Pending Mission: {doc.id} - Type: {data.get('mission_type')} - Created: {data.get('created_at')}")
        count += 1
    
    if count == 0:
        print("No PENDING missions found.")

except Exception as e:
    print(f"Error: {e}")
