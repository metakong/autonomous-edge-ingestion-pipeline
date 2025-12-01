import requests
import logging
import os
from google.cloud import storage
import time

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-REPLAY] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiReplay")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# --- THE HIJACK CONFIG ---
# Target URL
URL = "https://platform.getsporttrade.com/nfl"

# EXACT HEADERS FROM YOUR CURL (The "Human Suit")
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "referer": "https://new.getsporttrade.com/",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}

# COOKIES (From your -b flag)
COOKIES = {
    "_gcl_au": "1.1.1249508157.1764473371"
}

def execute_replay():
    logger.info(f"Replaying Human Session for: {URL}")
    try:
        # Request with exact headers/cookies
        response = requests.get(URL, headers=HEADERS, cookies=COOKIES, timeout=15)
        response.raise_for_status()
        
        html_content = response.text
        
        # VALIDATION: Did we get the app or the block?
        if "challenge-platform" in html_content or "Just a moment" in html_content:
            logger.error("FAILURE: Still hitting Cloudflare Challenge. Cookies might be expired.")
            return False
            
        logger.info(f"Success. Downloaded {len(html_content)} bytes.")
        
        # UPLOAD RAW HTML TO GCS
        # We upload the whole thing so the Brain can hunt for the fragmented data
        filename = f"sporttrade_dump_{int(time.time())}.html"
        blob = bucket.blob(f"raw_data/{filename}")
        blob.upload_from_string(html_content, content_type="text/html")
        
        logger.info(f"HTML Dumped: gs://{BUCKET_NAME}/raw_data/{filename}")
        
        # Save a local ref for the Cloud Brain to find later
        # (In a real run, we'd push this to Firestore, but for this test, just knowing the file exists is enough)
        return True

    except Exception as e:
        logger.error(f"Replay Failed: {e}")
        return False

if __name__ == "__main__":
    execute_replay()
