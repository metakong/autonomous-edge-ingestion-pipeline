import requests
import json
import time
import logging
from google.cloud import storage
import os
import sys
from fake_useragent import UserAgent

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import require_diagnosis, AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage

# LOGGING & CONFIG
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-GRAPHQL] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiGraphQL")
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)
ua = UserAgent()

# --- THE "DECODER RING" HEIST ---

# 1. The Endpoint
URL = "https://scorekeeper.prod.east.sporttrade.app/graphql"

# 2. The Payload (GraphQL Query)
# This asks for the event, markets, outcomes, and their IDs.
GRAPHQL_QUERY = """
query EventMarketsBySlug($slug: String!) {
  eventBySlug(slug: $slug) {
    id
    name
    markets {
      id
      name
      outcomes {
        id
        name
      }
    }
  }
}
"""
GRAPHQL_VARIABLES = {
    "slug": "pittsburgh-steelers-buffalo-bills-2025-11-30"
}

# 3. The Headers (Stealth Mode)
# We mimic a real browser to avoid being blocked.
HEADERS = {
    "User-Agent": ua.random,
    "Content-Type": "application/json",
    "Origin": "https://platform.getsporttrade.com",
    "Referer": "https://platform.getsporttrade.com/",
    # Important: Some APIs require a specific device ID or session.
    # If this fails, we may need to grab cookies from a real browser session.
    "x-device-id": "DELL-WORKER-v6" 
}

def validate_graphql_data(data: dict) -> bool:
    """Edge Data Integrity Check for GraphQL Response."""
    if not data:
        logger.error("Validation Failed: Empty response")
        return False
    if "data" not in data:
        logger.error("Validation Failed: 'data' key missing")
        return False
    if data["data"] is None:
        logger.error("Validation Failed: 'data' is null")
        return False
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info(f"Governance Check Passed. Initiating GraphQL Heist for: {GRAPHQL_VARIABLES['slug']}")
    start_time = time.time()
    
    try:
        # Send the POST request
        response = requests.post(
            URL,
            json={"query": GRAPHQL_QUERY, "variables": GRAPHQL_VARIABLES},
            headers=HEADERS,
            timeout=15
        )
        
        response.raise_for_status() # Raise an exception for bad status codes (4xx, 5xx)
        
        # Parse the JSON response
        data = response.json()
        
        # Verify we got data, not an error
        if "errors" in data:
             logger.error(f"GraphQL Error: {data['errors']}")
             return False

        if validate_graphql_data(data):
            logger.info("Heist Successful. Data acquired.")
            
            # --- HEAVY LIFTING TO GCS ---
            filename = f"graphql_decoder_{int(time.time())}.json"
            blob = bucket.blob(f"raw_data/{filename}")
            blob.upload_from_string(
                data=json.dumps(data, indent=2),
                content_type='application/json'
            )
            logger.info(f"Decoder Ring Uploaded: gs://{BUCKET_NAME}/raw_data/{filename}")
            
            # GENERATE EXECUTION REPORT
            report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_graphql",
                change_summary="GraphQL Event Data Query",
                primary_metric="bytes_secured",
                metric_before=0.0,
                metric_after=float(len(str(data))),
                observation_window_hours=0.01,
                success=True,
                notes=f"Secured: {len(str(data))} bytes of JSON"
            )
            
            # UPLOAD REPORT
            timestamp = int(time.time())
            report_filename = f"report_graphql_{timestamp}.json"
            blob_report = bucket.blob(f"governance/executions/{report_filename}")
            blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
            logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
            
            return True
        else:
            logger.warning("   -> GraphQL validation failed.")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_graphql",
                change_summary="GraphQL Query (FAILED)",
                primary_metric="bytes_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_graphql_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_graphql",
        human_readable_name="Acquisitions Officer (GraphQL)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need specific event metadata",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
