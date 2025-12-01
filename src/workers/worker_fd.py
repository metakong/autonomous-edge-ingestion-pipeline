import asyncio
import json
import time
import logging
import re
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker
class FanDuelWorker(BaseWorker):
    """
    Worker for scraping FanDuel odds using Playwright with Stealth.
    """
    TARGET_URL = "https://sportsbook.fanduel.com/navigation/nfl"

    def validate_fd_data(self, data: dict) -> bool:
        """Edge Data Integrity Check for FanDuel Data."""
        if not data:
            self.logger.error("Validation Failed: Data is empty")
            return False
        # Check for keys that indicate successful extraction of odds
        # This might be 'events', 'marketGroups', or similar depending on the structure
        # Since we are grabbing 'initialState', it should be a large object
        if len(str(data)) < 1000:
            self.logger.warning(f"Validation Warning: Data size suspiciously small ({len(str(data))} chars)")
            return False
        return True

    async def _run_async(self) -> bool:
        """
        Async implementation of the run logic.
        """
        self.logger.info("Launching Playwright (Stealth Mode) for FanDuel...")
        
        async with Stealth().use_async(async_playwright()) as p:
            # Launch browser (Headless for speed, but can be non-headless for debugging)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/Chicago"
            )
            page = await context.new_page()
            
            # STEALTH IS APPLIED AUTOMATICALLY BY THE WRAPPER
            
            try:
                self.logger.info(f"Navigating to {self.TARGET_URL}...")
                await page.goto(self.TARGET_URL, timeout=60000, wait_until="domcontentloaded")
                
                # Human pause to let React hydrate
                await page.wait_for_timeout(5000)
                
                # Check for soft blocks
                title = await page.title()
                content = await page.content()
                
                if "Error" in title or "Access Denied" in title or len(content) < 500:
                    self.logger.error(f"Soft Block Detected. Title: {title}")
                    await browser.close()
                    return False
                
                # Extract Data
                # --- DATA EXTRACTION STRATEGY ---
                data = None
                
                # Strategy 1: Global Variable 'initialState' (The Real Loot)
                try:
                    self.logger.info("Attempting Strategy 1: Extract window.initialState...")
                    # Try getting initialState directly
                    data = await page.evaluate("() => window.initialState || (typeof initialState !== 'undefined' ? initialState : null)")
                    if data:
                         self.logger.info("Strategy 1 Success: Captured 'initialState' global object.")
                except Exception as e:
                    self.logger.warning(f"Strategy 1 Failed: {e}")

                # Strategy 2: Regex + Browser Eval (Robust Fallback)
                if not data:
                    self.logger.info("Attempting Strategy 2: Regex extraction + Browser Eval...")
                    content = await page.content()
                    
                    # Find start of initialState assignment
                    # Pattern: initialState={ or ,initialState={
                    match = re.search(r'initialState\s*=\s*\{', content)
                    if match:
                        start_index = match.end() - 1 # Include opening brace
                        brace_count = 0
                        js_obj_str = ""
                        
                        # Extract the full JS object string by counting braces
                        for i in range(start_index, len(content)):
                            char = content[i]
                            js_obj_str += char
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                            
                            if brace_count == 0:
                                break
                        
                        if js_obj_str:
                            try:
                                # Use the browser to parse the JS object string!
                                # Wrap in parens to ensure it's treated as an expression
                                eval_expression = f"() => ({js_obj_str})"
                                data = await page.evaluate(eval_expression)
                                self.logger.info("Strategy 2 Success: Extracted and evaluated 'initialState' object.")
                            except Exception as e:
                                self.logger.warning(f"Strategy 2 Failed during eval: {e}")
                    else:
                        self.logger.warning("Strategy 2 Failed: Could not find 'initialState =' pattern.")

                # SAVE RESULTS
                timestamp = int(time.time())
                if data and self.validate_fd_data(data):
                    # We got structured data!
                    filename = f"results/fanduel_nfl_{timestamp}.json"
                    self.upload_json(data, filename)
                    
                    # GENERATE EXECUTION REPORT
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem="worker_fd",
                        change_summary="FanDuel NFL Odds Scrape",
                        primary_metric="bytes_secured",
                        metric_before=0.0,
                        metric_after=float(len(str(data))),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(str(data))} chars of JSON"
                    )
                    self.file_report(report)
                    
                    await browser.close()
                    return True
                else:
                    # Fallback to raw HTML
                    self.logger.warning("JSON Extraction Failed. Saving RAW HTML for analysis.")
                    filename = f"results/fanduel_nfl_raw_{timestamp}.json"
                    content = await page.content()
                    
                    self.upload_json({"raw_html": content}, filename)
                    
                    # Report Partial Success (Raw HTML)
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem="worker_fd",
                        change_summary="FanDuel Raw HTML Scrape",
                        primary_metric="bytes_secured",
                        metric_before=0.0,
                        metric_after=float(len(content)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(content)} bytes (Raw HTML)"
                    )
                    self.file_report(report)

                    await browser.close()
                    return True

            except Exception as e:
                self.logger.error(f"Heist Failed: {e}")
                # Generate Failure Report
                fail_report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_fd",
                    change_summary="FanDuel Scrape (FAILED)",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=0.0,
                    observation_window_hours=0.01,
                    success=False,
                    notes=str(e)
                )
                self.file_report(fail_report)
                
                await browser.close()
                return False

    def run(self) -> bool:
        """
        Entry point for the worker.
        """
        return asyncio.run(self._run_async())
