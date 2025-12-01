import requests
import json
import time
import os
import logging
import sys
from google.cloud import storage

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import require_diagnosis, AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-NOAA] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiNOAA")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# NOAA API (Weather.gov)
# User-Agent is REQUIRED by NOAA
HEADERS = {
    "User-Agent": "(veiled-vector-core, deardorff.sean@gmail.com)",
    "Accept": "application/geo+json"
}

# Target: Arrowhead Stadium (Kansas City)
LAT = "39.0489"
LON = "-94.4839"

def validate_forecast(data: dict) -> bool:
    """Edge Data Integrity Check for NOAA Forecast."""
    if not data:
        logger.error("Validation Failed: Empty response")
        return False
    if "properties" not in data:
        logger.error("Validation Failed: 'properties' key missing")
        return False
    if "periods" not in data["properties"]:
        logger.error("Validation Failed: 'periods' key missing in properties")
        return False
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Contacting National Weather Service...")
    start_time = time.time()
    
    try:
        # Step 1: Get Grid Point
        points_url = f"https://api.weather.gov/points/{LAT},{LON}"
        logger.info(f"Resolving grid for {LAT}, {LON}...")
        resp = requests.get(points_url, headers=HEADERS, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"Grid resolution failed: {resp.status_code} - {resp.text}")
            return False
            
        grid_data = resp.json()
        forecast_url = grid_data["properties"]["forecast"]
        
        # Step 2: Get Forecast
        logger.info(f"Fetching forecast from {forecast_url}...")
        forecast_resp = requests.get(forecast_url, headers=HEADERS, timeout=10)
        
        if forecast_resp.status_code == 200:
            data = forecast_resp.json()
            
            if validate_forecast(data):
                periods = data["properties"]["periods"]
                logger.info(f"Retrieved {len(periods)} forecast periods.")
                
                filename = f"noaa_arrowhead_{int(time.time())}.json"
                blob = bucket.blob(f"results/weather/{filename}")
                blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
                
                logger.info(f"LOOT SECURED: gs://{BUCKET_NAME}/results/weather/{filename}")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_noaa",
                    change_summary="NOAA Forecast Scrape",
                    primary_metric="periods_secured",
                    metric_before=0.0,
                    metric_after=float(len(periods)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(periods)} forecast periods"
                )
                
                # UPLOAD REPORT
                timestamp = int(time.time())
                report_filename = f"report_noaa_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
                
                return True
            else:
                logger.warning("   -> Forecast validation failed.")
                return False
        else:
            logger.error(f"Forecast failed: {forecast_resp.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_noaa",
                change_summary="NOAA Forecast Scrape (FAILED)",
                primary_metric="periods_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_noaa_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_03",
        human_readable_name="Acquisitions Officer (NOAA)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need atmospheric data for game modeling",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
