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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-PP] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiPP")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

TARGET_URL = "https://app.prizepicks.com/"

def validate_pp_data(data: dict) -> bool:
    """Edge Data Integrity Check for PrizePicks Data."""
    if not data:
        logger.error("Validation Failed: Data is empty")
        return False
    # Check for keys that indicate successful extraction
    # __NEXT_DATA__ usually has 'props' and 'pageProps'
    if "props" not in data:
        logger.warning("Validation Warning: 'props' key missing in __NEXT_DATA__")
        # It might still be valid, but suspicious
    if len(str(data)) < 1000:
        logger.warning(f"Validation Warning: Data size suspiciously small ({len(str(data))} chars)")
        return False
    return True

# --- THE GOVERNANCE GATE ---
# This decorator FORCES the caller to provide a DiagnosisReport.
@require_diagnosis
async def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Launching Playwright (Stealth Mode) for PrizePicks...")
    start_time = time.time()
    
    # WRAP PLAYWRIGHT WITH STEALTH
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
        
        # STEALTH IS APPLIED AUTOMATICALLY BY THE WRAPPER
        
        # Network Logging
        page.on("request", lambda request: logger.info(f">> {request.method} {request.url}"))
        page.on("response", lambda response: logger.info(f"<< {response.status} {response.url}"))

        try:
            logger.info(f"Navigating to {TARGET_URL}...")
            await page.goto(TARGET_URL, timeout=60000, wait_until="domcontentloaded")
            logger.info("Page loaded (DOM Content Loaded). Taking initial screenshot...")
            
            # Take immediate screenshot
            await page.screenshot(path="prizepicks_initial.png")
            
            # Human pause to let React hydrate (instead of strict networkidle)
            logger.info("Sleeping 10s for hydration...")
            await page.wait_for_timeout(10000)
            
            # Take post-hydration screenshot
            await page.screenshot(path="prizepicks_hydrated.png")
            logger.info("Screenshot taken: prizepicks_hydrated.png")
            
            # --- DATA EXTRACTION STRATEGY ---
            data = None
            
            # Strategy 1: __NEXT_DATA__ (Standard Next.js)
            try:
                logger.info("Attempting Strategy 1: Extract __NEXT_DATA__...")
                data = await page.evaluate("() => window.__NEXT_DATA__")
                if data:
                    logger.info("Strategy 1 Success: Captured '__NEXT_DATA__'.")
            except Exception as e:
                logger.warning(f"Strategy 1 Failed: {e}")

            # SAVE RESULTS
            timestamp = int(time.time())
            if data and validate_pp_data(data):
                # We got structured data!
                filename = f"prizepicks_{timestamp}.json"
                blob = bucket.blob(f"results/{filename}")
                blob.upload_from_string(json.dumps(data), content_type="application/json")
                logger.info(f"LOOT SECURED: gs://{BUCKET_NAME}/results/{filename}")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_pp",
                    change_summary="PrizePicks Odds Scrape",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=float(len(str(data))),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(str(data))} chars of JSON"
                )
                
                # UPLOAD REPORT
                report_filename = f"report_pp_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
                
                return True 
            else:
                # Fallback to raw HTML
                logger.warning("JSON Extraction Failed. Saving RAW HTML for analysis.")
                filename = f"prizepicks_raw_{timestamp}.json"
                content = await page.content()
                blob = bucket.blob(f"results/{filename}")
                blob.upload_from_string(json.dumps({"raw_html": content}), content_type="application/json")
                logger.info(f"RAW HTML SAVED: gs://{BUCKET_NAME}/results/{filename}")
                
                # Report Partial Success (Raw HTML)
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_pp",
                    change_summary="PrizePicks Raw HTML Scrape",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=float(len(content)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(content)} bytes (Raw HTML)"
                )
                report_filename = f"report_pp_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                
                return True

        except Exception as e:
            logger.error(f"Mission Failed: {e}")
            # Generate Failure Report
            try:
                fail_report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_pp",
                    change_summary="PrizePicks Scrape (FAILED)",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=0.0,
                    observation_window_hours=0.01,
                    success=False,
                    notes=str(e)
                )
                timestamp = int(time.time())
                blob_fail = bucket.blob(f"governance/executions/fail_pp_{timestamp}.json")
                blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
            except Exception as report_error:
                logger.error(f"Could not file failure report: {report_error}")
            
            return False # Indicate failure
        finally:
            await browser.close()


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
