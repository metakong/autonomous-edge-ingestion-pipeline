import requests
import json
import logging
import os
from fake_useragent import UserAgent

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-DEBUG] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiDebug")

# CONFIG
BASE_URL = "https://api.prod.east.sporttrade.app/api"
ua = UserAgent()

# ENHANCED HEADERS (The "VIP" Suit)
HEADERS = {
    "User-Agent": ua.random,
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://platform.getsporttrade.com/",
    "Origin": "https://platform.getsporttrade.com",
    # KEYS FOUND IN YOUR HTML
    "X-XPoint-Client": "strader",
    "X-Client-Platform": "web" 
}

def probe_endpoint(suffix):
    url = f"{BASE_URL}/{suffix}"
    logger.info(f"Probing: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        # 1. Log Status
        logger.info(f"Status: {response.status_code}")
        
        # 2. Log Raw Body (First 500 chars) - THIS IS CRITICAL
        logger.info(f"Raw Response: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                logger.error("Failed to parse JSON (See Raw Response above)")
                return None
        return None
    except Exception as e:
        logger.error(f"Error probing {suffix}: {e}")
        return None

def run_debug():
    # Target the specific contest ID we saw in your logs ('buf5c')
    # and the generic lists
    endpoints = [
        "v1/competitions",
        "v1/events/buf5c" 
    ]

    for ep in endpoints:
        probe_endpoint(ep)

if __name__ == "__main__":
    run_debug()
