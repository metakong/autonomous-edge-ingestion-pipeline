import socketio
import logging
import json
import time
import os
import sys
from google.cloud import storage

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import require_diagnosis, AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-PLATFORM] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiPlatform")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# TARGET: The Metadata Server
URL = "https://platform.getsporttrade.com"

sio = socketio.Client(logger=True, engineio_logger=True)

# CAPTURE BUFFER
captured_events = []

# THE LIST OF ACTIVE GAMES (Derived from your logs)
SUBSCRIPTION_PAYLOAD = [
    "buf5c","bufqc","buotc","buo1c","buowc","buoic","buouc","buosc",
    "buozc","buoac","buo3c","buo4c","buorc","buoyc","bug7c","bufpc",
    "bufhc","buf6c","bux4c","bufzc","buxec","bufac","bugdc","buodc",
    "buq6c","bu8gc","bugcc","bufcc","bugec","bugmc","bu8yc","bug3c",
    "buf1c","bufsc","buguc","buxxc","bugnc","bugfc","bu8rc","buftc",
    "buggc","bug5c","bumsc","buxqc","buq9c","buf3c","bufuc","bux7c",
    "bugpc","bug6c","bux3c","bux9c","buxwc","bufxc","bugzc","bugac",
    "bug8c","bug9c","bugbc","bu8nc","bu8dc","buf7c","bugkc","bu8fc",
    "buf9c","bugsc","buf4c","bugyc","bu8bc"
]

@sio.event
def connect():
    logger.info("CONNECTED to PLATFORM!")
    # THE KEY STEP: Ask for the data
    logger.info(f"Sending Subscription...")
    sio.emit('subscribe', SUBSCRIPTION_PAYLOAD)

@sio.on('*')
def catch_all(event, data):
    logger.info(f"RECEIVED EVENT: {event}")
    
    # Check for the Rosetta Stone
    text_dump = json.dumps(data)
    if "Buffalo" in text_dump or "Steelers" in text_dump:
        logger.info(">>> TARGET ACQUIRED (Names Found!) <<<")
    
    captured_events.append({"type": event, "data": data})

def validate_platform_data(events: list) -> bool:
    """Edge Data Integrity Check for Platform Events."""
    if not events:
        logger.error("Validation Failed: No events captured")
        return False
    if len(events) < 5: # Arbitrary minimum
        logger.warning(f"Validation Warning: Low event count ({len(events)})")
        # Still return True as it might be a quiet time
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Connecting to Platform...")
    start_time = time.time()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Origin": "https://platform.getsporttrade.com"
    }
    
    try:
        sio.connect(URL, headers=headers, transports=['websocket'])
        
        # Listen for 15 seconds
        time.sleep(15)
        
        logger.info("Session complete. Uploading capture...")
        
        if validate_platform_data(captured_events):
            filename = f"platform_dump_{int(time.time())}.json"
            blob = bucket.blob(f"raw_data/{filename}")
            blob.upload_from_string(json.dumps(captured_events, default=str), content_type='application/json')
            
            logger.info(f"Data Secured: gs://{BUCKET_NAME}/raw_data/{filename}")
            sio.disconnect()
            
            # GENERATE EXECUTION REPORT
            report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_platform",
                change_summary="SportTrade Platform Socket Capture",
                primary_metric="events_captured",
                metric_before=0.0,
                metric_after=float(len(captured_events)),
                observation_window_hours=0.01,
                success=True,
                notes=f"Secured: {len(captured_events)} events"
            )
            
            # UPLOAD REPORT
            timestamp = int(time.time())
            report_filename = f"report_platform_{timestamp}.json"
            blob_report = bucket.blob(f"governance/executions/{report_filename}")
            blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
            logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
            
            return True
        else:
            logger.warning("   -> Platform data validation failed.")
            sio.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"Platform Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_platform",
                change_summary="Platform Capture (FAILED)",
                primary_metric="events_captured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_platform_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_platform",
        human_readable_name="Acquisitions Officer (SportTrade Platform)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need real-time market liquidity data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
