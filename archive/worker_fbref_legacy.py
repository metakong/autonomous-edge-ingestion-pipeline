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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-FBREF] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiFBref")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# FBref (Soccer xG)
# Target: Premier League Stats
TARGET_URL = "https://fbref.com/en/comps/9/Premier-League-Stats"

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
    logger.info("Governance Check Passed. Checking VAR (FBref)...")
    start_time = time.time()
    items_secured = []
    
    try:
        logger.info(f"Scraping {TARGET_URL}...")
        # Pandas read_html is excellent for Sports Reference sites
        # But they have rate limits. We must be careful.
        # Adding a sleep to be polite if this were a loop.
        
        dfs = pd.read_html(TARGET_URL)
        
        if dfs:
            # Usually the first table is the standings
            standings = dfs[0]
            if validate_dataframe(standings, "Standings"):
                filename = f"fbref_pl_standings_{int(time.time())}.csv"
                blob = bucket.blob(f"results/soccer/{filename}")
                blob.upload_from_string(standings.to_csv(index=False), content_type='text/csv')
                logger.info(f"   -> Standings Secured: {len(standings)} teams.")
                items_secured.append(f"Standings ({len(standings)} rows)")
            
            # Often there are more tables (Squad Stats, etc)
            if len(dfs) > 1:
                stats = dfs[1] # Hypothetical
                if validate_dataframe(stats, "Squad Stats"):
                    filename_stats = f"fbref_pl_stats_{int(time.time())}.csv"
                    blob_stats = bucket.blob(f"results/soccer/{filename_stats}")
                    blob_stats.upload_from_string(stats.to_csv(index=False), content_type='text/csv')
                    logger.info(f"   -> Squad Stats Secured.")
                    items_secured.append(f"Squad Stats ({len(stats)} rows)")
            
            # GENERATE EXECUTION REPORT
            report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_fbref",
                change_summary="FBref PL Stats Scrape",
                primary_metric="tables_secured",
                metric_before=0.0,
                metric_after=float(len(items_secured)),
                observation_window_hours=0.01,
                success=True,
                notes=f"Secured: {', '.join(items_secured)}"
            )
            
            # UPLOAD REPORT
            timestamp = int(time.time())
            report_filename = f"report_fbref_{timestamp}.json"
            blob_report = bucket.blob(f"governance/executions/{report_filename}")
            blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
            logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
            
            return True
        else:
            logger.error("   -> No tables found.")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_fbref",
                change_summary="FBref Scrape (FAILED)",
                primary_metric="tables_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_fbref_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_fbref",
        human_readable_name="Acquisitions Officer (FBref)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need soccer xG data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
