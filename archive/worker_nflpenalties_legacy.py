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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-NFLPENALTIES] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiNFLPenalties")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

TARGET_URL = "https://www.nflpenalties.com/all-positions.php?year=2024"

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
    logger.info("Governance Check Passed. Flag on the play (NFLPenalties.com)...")
    start_time = time.time()
    
    try:
        logger.info(f"Scraping {TARGET_URL}...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        resp = requests.get(TARGET_URL, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Find the main table
            table = soup.find('table', {'class': 'table'})
            if table:
                # Parse with Pandas
                df = pd.read_html(str(table))[0]
                
                if validate_dataframe(df, "Penalties Table"):
                    filename = f"nfl_penalties_2024_{int(time.time())}.csv"
                    blob = bucket.blob(f"results/nfl/{filename}")
                    blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                    logger.info(f"   -> Flags Secured: {len(df)} rows.")
                    
                    # GENERATE EXECUTION REPORT
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem="worker_nflpenalties",
                        change_summary="NFL Penalties Scrape",
                        primary_metric="rows_secured",
                        metric_before=0.0,
                        metric_after=float(len(df)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(df)} rows"
                    )
                    
                    # UPLOAD REPORT
                    timestamp = int(time.time())
                    report_filename = f"report_nflpenalties_{timestamp}.json"
                    blob_report = bucket.blob(f"governance/executions/{report_filename}")
                    blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                    logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
                    
                    return True
                else:
                    logger.warning("   -> Dataframe validation failed.")
                    return False
            else:
                logger.error("   -> Table not found in HTML.")
                return False
        else:
            logger.error(f"Scrape failed: {resp.status_code}")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_nflpenalties",
                change_summary="NFL Penalties Scrape (FAILED)",
                primary_metric="rows_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_nflpenalties_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_nflpenalties",
        human_readable_name="Acquisitions Officer (NFL Penalties)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need referee tendency data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
