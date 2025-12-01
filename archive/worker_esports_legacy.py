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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-ESPORTS] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiEsports")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# Oracle's Elixir LoL Data (2024)
CSV_URL = "https://oracleselixir-downloadable-match-data.s3-us-west-2.amazonaws.com/2024_LoL_esports_match_data_from_OraclesElixir.csv"

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
    logger.info("Governance Check Passed. Entering Summoner's Rift (Oracle's Elixir)...")
    start_time = time.time()
    
    try:
        logger.info(f"Downloading 2024 LoL Match Data from {CSV_URL}...")
        
        # Read directly
        df = pd.read_csv(CSV_URL)
        
        if validate_dataframe(df, "LoL Matches"):
            filename = f"lol_matches_2024_{int(time.time())}.csv"
            blob = bucket.blob(f"results/esports/{filename}")
            blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
            logger.info(f"   -> Nexus Destroyed: {len(df)} rows secured.")
            
            # GENERATE EXECUTION REPORT
            report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_esports",
                change_summary="LoL Match Data Scrape",
                primary_metric="rows_secured",
                metric_before=0.0,
                metric_after=float(len(df)),
                observation_window_hours=0.01,
                success=True,
                notes=f"Secured: {len(df)} rows"
            )
            
            # UPLOAD REPORT
            timestamp = int(time.time())
            report_filename = f"report_esports_{timestamp}.json"
            blob_report = bucket.blob(f"governance/executions/{report_filename}")
            blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
            logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
            
            return True
        else:
            logger.warning("   -> No data found.")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_esports",
                change_summary="LoL Match Data Scrape (FAILED)",
                primary_metric="rows_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_esports_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_esports",
        human_readable_name="Acquisitions Officer (Esports)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need LoL match data for early game analysis",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
