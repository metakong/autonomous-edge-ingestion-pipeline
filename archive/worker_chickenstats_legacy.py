import chickenstats as cs
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-CHICKEN] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiChicken")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Faceoff (Evolving Hockey via ChickenStats)...")
    start_time = time.time()
    
    try:
        logger.warning("ChickenStats primarily processes local CSVs from Evolving Hockey.")
        logger.info("   -> Evolving Hockey requires paid subscription CSVs.")
        logger.info("   -> Marking as 'Ready for Ingestion' once files are present.")
        
        # GENERATE EXECUTION REPORT (Placeholder Success)
        report = ExecutionReport(
            stage=DSIEStage.EXECUTE,
            subsystem="worker_chickenstats",
            change_summary="Evolving Hockey Placeholder Check",
            primary_metric="files_processed",
            metric_before=0.0,
            metric_after=0.0,
            observation_window_hours=0.01,
            success=True,
            notes="Placeholder: Waiting for manual CSV upload."
        )
        
        # UPLOAD REPORT
        timestamp = int(time.time())
        report_filename = f"report_chickenstats_{timestamp}.json"
        blob_report = bucket.blob(f"governance/executions/{report_filename}")
        blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
        logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
        
        return True

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_chickenstats",
                change_summary="Evolving Hockey Placeholder (FAILED)",
                primary_metric="files_processed",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_chickenstats_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_chicken",
        human_readable_name="Acquisitions Officer (ChickenStats)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need advanced hockey metrics",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
