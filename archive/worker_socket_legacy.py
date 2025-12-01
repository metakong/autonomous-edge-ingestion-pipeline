import socketio
import logging
import json
import time
import os
from google.cloud import storage

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-SNIFFER] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiSniffer")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

URL = "https://platform.getsporttrade.com"
sio = socketio.Client(logger=True, engineio_logger=True)

# CAPTURE BUFFER
captured_events = []
start_time = 0

@sio.event
def connect():
    logger.info("CONNECTED! Waiting for data...")
    global start_time
    start_time = time.time()

@sio.on('*')
def catch_all(event, data):
    logger.info(f"EVENT: {event}")
    # Log a snippet so we can see what it is
    snippet = str(data)[:500] 
    logger.info(f"PAYLOAD (Snippet): {snippet}")
    
    captured_events.append({"event": event, "data": data})
    
    # Dump to disk if we find something big
    if len(str(data)) > 1000:
        logger.info("Found LARGE payload. Likely the Map.")

@sio.event
def disconnect():
    logger.info("Disconnected.")

def run_sniffer():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Origin": "https://platform.getsporttrade.com"
    }
    
    try:
        sio.connect(URL, headers=headers, transports=['websocket'])
        
        # Listen for 15 seconds then kill it
        time.sleep(15)
        
        logger.info("Sniffing complete. Uploading capture...")
        
        # Upload whatever we found
        filename = f"socket_sniff_{int(time.time())}.json"
        blob = bucket.blob(f"raw_data/{filename}")
        blob.upload_from_string(json.dumps(captured_events, default=str), content_type='application/json')
        
        logger.info(f"Capture uploaded: gs://{BUCKET_NAME}/raw_data/{filename}")
        sio.disconnect()
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    run_sniffer()
