import asyncio
import json
import time
from typing import Optional

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from src.base_worker import BaseWorker


class PrizePicksWorker(BaseWorker):
    """
    Worker for scraping PrizePicks odds using Playwright with Stealth.
    """
    TARGET_URL = "https://app.prizepicks.com/"
    _WORKER_ID = "prizepicks_worker"

    def validate_pp_data(self, data: dict) -> bool:
        """Edge Data Integrity Check for PrizePicks Data."""
        if not data:
            self.logger.error("Validation Failed: Data is empty")
            return False
        if "props" not in data:
            self.logger.warning("Validation Warning: 'props' key missing in __NEXT_DATA__")
        if len(str(data)) < 1000:
            self.logger.warning(
                f"Validation Warning: Data size suspiciously small ({len(str(data))} chars)"
            )
            return False
        return True

    async def _run_async(self) -> bool:
        """Async implementation of the run logic, since Playwright is async."""
        self.logger.info("Launching Playwright (Stealth Mode) for PrizePicks...")

        async with Stealth().use_async(async_playwright()) as p:
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
                ignore_default_args=["--enable-automation"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/Chicago",
                java_script_enabled=True,
            )
            page = await context.new_page()

            # Mask the webdriver flag so bot-detection scripts see a normal browser
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )

            # Network logging (debug aid — comment out in production to reduce noise)
            page.on(
                "request",
                lambda request: self.logger.debug(f">> {request.method} {request.url}"),
            )
            page.on(
                "response",
                lambda response: self.logger.debug(f"<< {response.status} {response.url}"),
            )

            try:
                self.logger.info(f"Navigating to {self.TARGET_URL}...")
                await page.goto(
                    self.TARGET_URL, timeout=60000, wait_until="domcontentloaded"
                )

                # Take an initial screenshot for debugging/verification
                timestamp = int(time.time())
                screenshot_bytes = await page.screenshot()
                blob = self.bucket.blob(
                    f"screenshots/{self._WORKER_ID}_{timestamp}_initial.png"
                )
                blob.upload_from_string(screenshot_bytes, content_type="image/png")
                self.logger.info(
                    f"Screenshot uploaded: screenshots/{self._WORKER_ID}_{timestamp}_initial.png"
                )

                # Allow React to fully hydrate the page
                self.logger.info("Sleeping 10s for hydration...")
                await page.wait_for_timeout(10000)

                # Post-hydration screenshot
                screenshot_bytes = await page.screenshot()
                blob = self.bucket.blob(
                    f"screenshots/{self._WORKER_ID}_{timestamp}_hydrated.png"
                )
                blob.upload_from_string(screenshot_bytes, content_type="image/png")
                self.logger.info(
                    f"Screenshot uploaded: screenshots/{self._WORKER_ID}_{timestamp}_hydrated.png"
                )

                # --- DATA EXTRACTION STRATEGY ---
                data: Optional[dict] = None

                # Strategy 1: __NEXT_DATA__ (Standard Next.js global)
                try:
                    self.logger.info("Attempting Strategy 1: Extract __NEXT_DATA__...")
                    data = await page.evaluate("() => window.__NEXT_DATA__")
                    if data:
                        self.logger.info(
                            "Strategy 1 Success: Captured '__NEXT_DATA__'."
                        )
                except Exception as e:
                    self.logger.warning(f"Strategy 1 Failed: {e}")

                # SAVE RESULTS
                timestamp = int(time.time())
                if data and self.validate_pp_data(data):
                    filename = f"results/prizepicks_{timestamp}.json"
                    self.upload_json(data, filename)
                    return True
                else:
                    # Fallback: save raw HTML for offline analysis
                    self.logger.warning(
                        "JSON Extraction Failed. Saving RAW HTML for analysis."
                    )
                    filename = f"results/prizepicks_raw_{timestamp}.json"
                    content = await page.content()
                    self.upload_json({"raw_html": content}, filename)
                    return True

            except Exception as e:
                self.logger.error(f"Mission Failed: {e}")
                return False
            finally:
                # Always clean up the browser, regardless of success or failure
                await browser.close()

    def run(self) -> bool:
        """Entry point for the worker. Runs the async logic synchronously."""
        return asyncio.run(self._run_async())
