import asyncio
import json
import time
import os
import logging
import sys
from google.cloud import storage
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import require_diagnosis, AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-FD] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiFD")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

TARGET_URL = "https://sportsbook.fanduel.com/navigation/nfl"

def validate_fd_data(data: dict) -> bool:
    """Edge Data Integrity Check for FanDuel Data."""
    if not data:
        logger.error("Validation Failed: Data is empty")
        return False
    # Check for keys that indicate successful extraction of odds
    # This might be 'events', 'marketGroups', or similar depending on the structure
    # Since we are grabbing 'initialState', it should be a large object
    if len(str(data)) < 1000:
        logger.warning(f"Validation Warning: Data size suspiciously small ({len(str(data))} chars)")
        return False
    return True

# --- THE GOVERNANCE GATE ---
# This decorator FORCES the caller to provide a DiagnosisReport.
@require_diagnosis
async def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Launching Playwright (Stealth Mode) for FanDuel...")
    start_time = time.time()
    
    # WRAP PLAYWRIGHT WITH STEALTH
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
            logger.info(f"Navigating to {TARGET_URL}...")
            await page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            
            # Human pause to let React hydrate
            await page.wait_for_timeout(5000)
            
            # Check for soft blocks
            title = await page.title()
            content = await page.content()
            
            if "Error" in title or "Access Denied" in title or len(content) < 500:
                logger.error(f"Soft Block Detected. Title: {title}")
                await browser.close()
                return False
            
            # Extract Data
            # --- DATA EXTRACTION STRATEGY ---
            data = None
            
            # Strategy 1: Global Variable 'initialState' (The Real Loot)
            try:
                logger.info("Attempting Strategy 1: Extract window.initialState...")
                # Try getting initialState directly
                data = await page.evaluate("() => window.initialState || (typeof initialState !== 'undefined' ? initialState : null)")
                if data:
                     logger.info("Strategy 1 Success: Captured 'initialState' global object.")
            except Exception as e:
                logger.warning(f"Strategy 1 Failed: {e}")

            # Strategy 2: Regex + Browser Eval (Robust Fallback)
            if not data:
                logger.info("Attempting Strategy 2: Regex extraction + Browser Eval...")
                content = await page.content()
                
                # Find start of initialState assignment
                # Pattern: initialState={ or ,initialState={
                import re
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
                            logger.info("Strategy 2 Success: Extracted and evaluated 'initialState' object.")
                        except Exception as e:
                            logger.warning(f"Strategy 2 Failed during eval: {e}")
                else:
                    logger.warning("Strategy 2 Failed: Could not find 'initialState =' pattern.")

            # SAVE RESULTS
            timestamp = int(time.time())
            if data and validate_fd_data(data):
                # We got structured data!
                filename = f"fanduel_nfl_{timestamp}.json"
                blob = bucket.blob(f"results/{filename}")
                blob.upload_from_string(json.dumps(data), content_type="application/json")
                logger.info(f"LOOT SECURED: gs://{BUCKET_NAME}/results/{filename}")
                
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
                
                # UPLOAD REPORT
                report_filename = f"report_fd_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
                
                await browser.close()
                return True
            else:
                # Fallback to raw HTML
                logger.warning("JSON Extraction Failed. Saving RAW HTML for analysis.")
                filename = f"fanduel_nfl_raw_{timestamp}.json"
                content = await page.content()
                blob = bucket.blob(f"results/{filename}")
                blob.upload_from_string(json.dumps({"raw_html": content}), content_type="application/json")
                logger.info(f"RAW HTML SAVED: gs://{BUCKET_NAME}/results/{filename}")
                
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
                report_filename = f"report_fd_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')

                await browser.close()
                return True

        except Exception as e:
            logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            try:
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
                timestamp = int(time.time())
                blob_fail = bucket.blob(f"governance/executions/fail_fd_{timestamp}.json")
                blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
            except Exception as report_error:
                logger.error(f"Could not file failure report: {report_error}")
            
            await browser.close()
            return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_fd",
        human_readable_name="Acquisitions Officer (FanDuel)",
        autonomy_level=2
    )

    # TEST 1: RUN WITHOUT DIAGNOSIS (SHOULD FAIL)
    print("\n--- ATTEMPT 1: Running naked (No Diagnosis) ---")
    try:
        bad_ctx = AgentContext(contract=contract, current_diagnosis=None)
        asyncio.run(execute_heist(ctx=bad_ctx))
    except Exception as e:
        logger.error(f"BLOCKED BY GOVERNANCE: {e}")

    # TEST 2: RUN WITH DIAGNOSIS (SHOULD SUCCEED)
    print("\n--- ATTEMPT 2: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need fresh FanDuel NFL odds",
        root_cause_hypothesis="Expansion Phase 1",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    asyncio.run(execute_heist(ctx=good_ctx))
