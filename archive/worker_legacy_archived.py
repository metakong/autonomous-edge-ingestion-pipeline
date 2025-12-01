import os
import time
import json
import logging
import random
from google.cloud import firestore
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
import asyncio
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-WORKER] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiWorker")
db = firestore.Client(database="veiled-vector-core-firestore")
ua = UserAgent()

async def scrape_target(url: str):
    logger.info(f"Targeting: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=ua.random,
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        # Bypass some bot detections
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        try:
            # Load the page
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Wait for the ODDS to physically render
            # We wait for a generic class that usually holds match data to ensure hydration
            try:
                await page.wait_for_selector("div[class*='flex']", timeout=15000)
            except:
                logger.warning("Could not find specific match selectors, proceeding with full dump.")
            
            await page.wait_for_timeout(5000) # Extra buffer
            
            # 1. CAPTURE EVIDENCE (Screenshot)
            screenshot_bytes = await page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # 2. CAPTURE RAW DATA (No Cleaning)
            content = await page.content()
            title = await page.title()
            
            await browser.close()
            
            # We return the FULL HTML. It's heavy, but it contains the hidden JSON state.
            return {
                "status": "SUCCESS", 
                "title": title, 
                "data": content, # RAW HTML
                "screenshot": screenshot_b64 
            }
        except Exception as e:
            await browser.close()
            return {"status": "FAILED", "error": str(e)}

async def process_mission(doc):
    mission_data = doc.to_dict()
    task = mission_data.get("task")
    
    # Direct Target
    target_url = "https://www.oddsportal.com/american-football/usa/nfl/"
    
    logger.info(f"Executing: {target_url}")
    result = await scrape_target(target_url)
    
    if result["status"] == "SUCCESS":
        # Verify we actually got data, not just a title
        if len(result["data"]) < 5000:
             logger.error("Page suspiciously small. Likely blocked.")
             doc.reference.update({"status": "FAILED", "error": "Soft Block (Empty Body)"})
             return

        doc.reference.update({
            "status": "COMPLETED",
            "result_data": result["data"], # Raw HTML
            "result_title": result["title"],
            "result_screenshot": result["screenshot"], # Visual Proof
            "completed_at": firestore.SERVER_TIMESTAMP
        })
        logger.info("Mission Success. Raw Data Uploaded.")
    else:
        logger.error(f"Mission Failed: {result['error']}")
        doc.reference.update({"status": "FAILED", "error": result['error']})

async def main_loop():
    logger.info("KAJI RAW-WORKER ONLINE.")
    while True:
        try:
            docs = db.collection("mission_queue").where("status", "==", "PENDING").limit(1).stream()
            found = False
            for doc in docs:
                found = True
                await process_mission(doc)
            if not found: time.sleep(5)
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main_loop())
