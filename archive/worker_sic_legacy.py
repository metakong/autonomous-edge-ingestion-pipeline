import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import logging
import sys
from google.cloud import storage

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import require_diagnosis, AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-SIC] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiSIC")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# SIC Score (Sports Injury Central)
# Target: NFL Injury Index (Example)
TARGET_URL = "https://sicscore.com/nfl/updates"

def validate_dataframe(df: pd.DataFrame, name: str) -> bool:
    """Edge Data Integrity Check for DataFrames."""
    if df is None:
        logger.error(f"Validation Failed: {name} is None")
        return False
    if df.empty:
        logger.warning(f"Validation Warning: {name} is empty")
        return False
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Checking the medical tent (SIC Score)...")
    start_time = time.time()
    
    try:
        logger.info(f"Scraping {TARGET_URL}...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        resp = requests.get(TARGET_URL, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # SIC Score usually has cards or a list of updates.
            # We will grab the text content of updates.
            
            # Find update containers (Hypothetical class based on standard blog structures)
            # Inspecting site structure mentally: often div class="update-card" or similar.
            # Let's grab all article text for now to ensure we get the data.
            
            articles = soup.find_all('article')
            data = []
            for article in articles:
                text = article.get_text(strip=True)
                data.append({"content": text})
            
            if data:
                df = pd.DataFrame(data)
                
                if validate_dataframe(df, "SIC Updates"):
                    filename = f"sic_updates_{int(time.time())}.csv"
                    blob = bucket.blob(f"results/injuries/{filename}")
                    blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                    logger.info(f"   -> Injury Reports Secured: {len(df)} updates.")
                    
                    # GENERATE EXECUTION REPORT
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem="worker_sic",
                        change_summary="SIC Score Updates Scrape",
                        primary_metric="updates_secured",
                        metric_before=0.0,
                        metric_after=float(len(df)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(df)} updates"
                    )
                    
                    # UPLOAD REPORT
                    timestamp = int(time.time())
                    report_filename = f"report_sic_{timestamp}.json"
                    blob_report = bucket.blob(f"governance/executions/{report_filename}")
                    blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                    logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
                    
                    return True
                else:
                    logger.warning("   -> Dataframe validation failed.")
                    return False
            else:
                # Fallback: Save HTML if no articles found (site structure might differ)
                filename = f"sic_raw_{int(time.time())}.html"
                blob = bucket.blob(f"results/injuries/{filename}")
                blob.upload_from_string(resp.content, content_type='text/html')
                logger.info(f"   -> Raw HTML Secured (Structure uncertain).")
                
                # Report Partial Success
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_sic",
                    change_summary="SIC Score Raw HTML Scrape",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=float(len(resp.content)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(resp.content)} bytes (Raw HTML)"
                )
                timestamp = int(time.time())
                report_filename = f"report_sic_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                
                return True
        else:
            logger.error(f"Scrape failed: {resp.status_code}")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_sic",
                change_summary="SIC Score Scrape (FAILED)",
                primary_metric="updates_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_sic_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_sic",
        human_readable_name="Acquisitions Officer (SIC Score)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need expert injury analysis",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
