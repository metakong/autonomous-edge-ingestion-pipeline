import asyncio
import json
import time
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class PrizePicksWorker(BaseWorker):
    """
    Worker for scraping PrizePicks odds using Playwright with Stealth.
    """
    TARGET_URL = "https://app.prizepicks.com/"

    def validate_pp_data(self, data: dict) -> bool:
        """Edge Data Integrity Check for PrizePicks Data."""
        if not data:
            self.logger.error("Validation Failed: Data is empty")
            return False
        # Check for keys that indicate successful extraction
        # __NEXT_DATA__ usually has 'props' and 'pageProps'
        if "props" not in data:
            self.logger.warning("Validation Warning: 'props' key missing in __NEXT_DATA__")
            # It might still be valid, but suspicious
        if len(str(data)) < 1000:
            self.logger.warning(f"Validation Warning: Data size suspiciously small ({len(str(data))} chars)")
            return False
        return True

    async def _run_async(self) -> bool:
        """
        Async implementation of the run logic, since Playwright is async.
        """
        self.logger.info("Launching Playwright (Stealth Mode) for PrizePicks...")
        
        async with Stealth().use_async(async_playwright()) as p:
            # Launch browser with HARDENED STEALTH ARGS
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                ],
                ignore_default_args=["--enable-automation"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/Chicago",
                java_script_enabled=True,
            )
            page = await context.new_page()
            
            # Add init script to mask webdriver
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Network Logging
            page.on("request", lambda request: self.logger.info(f">> {request.method} {request.url}"))
            page.on("response", lambda response: self.logger.info(f"<< {response.status} {response.url}"))

            try:
                self.logger.info(f"Navigating to {self.TARGET_URL}...")
                await page.goto(self.TARGET_URL, timeout=60000, wait_until="domcontentloaded")
                self.logger.info("Page loaded (DOM Content Loaded). Taking initial screenshot...")
                
                # Take immediate screenshot
                screenshot_bytes = await page.screenshot()
                timestamp = int(time.time())
                blob = self.bucket.blob(f"screenshots/{self.context.contract.agent_id}_{timestamp}_initial.png")
                blob.upload_from_string(screenshot_bytes, content_type='image/png')
                self.logger.info(f"Screenshot uploaded: screenshots/{self.context.contract.agent_id}_{timestamp}_initial.png")
                
                # Human pause to let React hydrate
                self.logger.info("Sleeping 10s for hydration...")
                await page.wait_for_timeout(10000)
                
                # Take post-hydration screenshot
                screenshot_bytes = await page.screenshot()
                blob = self.bucket.blob(f"screenshots/{self.context.contract.agent_id}_{timestamp}_hydrated.png")
                blob.upload_from_string(screenshot_bytes, content_type='image/png')
                self.logger.info(f"Screenshot uploaded: screenshots/{self.context.contract.agent_id}_{timestamp}_hydrated.png")
                
                # --- DATA EXTRACTION STRATEGY ---
                data = None
                
                # Strategy 1: __NEXT_DATA__ (Standard Next.js)
                try:
                    self.logger.info("Attempting Strategy 1: Extract __NEXT_DATA__...")
                    data = await page.evaluate("() => window.__NEXT_DATA__")
                    if data:
                        self.logger.info("Strategy 1 Success: Captured '__NEXT_DATA__'.")
                except Exception as e:
                    self.logger.warning(f"Strategy 1 Failed: {e}")

                # SAVE RESULTS
                timestamp = int(time.time())
                if data and self.validate_pp_data(data):
                    # We got structured data!
                    filename = f"results/prizepicks_{timestamp}.json"
                    self.upload_json(data, filename)
                    
                    # GENERATE EXECUTION REPORT
                    return True 
                else:
                    # Fallback to raw HTML
                    self.logger.warning("JSON Extraction Failed. Saving RAW HTML for analysis.")
                    filename = f"results/prizepicks_raw_{timestamp}.json"
                    content = await page.content()
                    
                    # Upload raw html as json wrapper
                    self.upload_json({"raw_html": content}, filename)
                    
                    # Report Partial Success (Raw HTML)
                    return True

            except Exception as e:
                self.logger.error(f"Mission Failed: {e}")
                # Generate Failure Report
                return False
            finally:
                await browser.close()

    def run(self) -> bool:
        """
        Entry point for the worker. Runs the async logic.
        """
        return asyncio.run(self._run_async())
