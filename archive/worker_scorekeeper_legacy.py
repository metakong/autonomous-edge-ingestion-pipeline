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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-KEEPER] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiKeeper")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# TARGET: The Data Server
URL = "https://scorekeeper.prod.east.sporttrade.app"

sio = socketio.Client(logger=True, engineio_logger=True)

# CAPTURE BUFFER
captured_events = []

# HARDCODED CONTEST IDS (Scraped from your previous logs)
# These represent "Active Games" or "Leagues"
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
    logger.info("CONNECTED to SCOREKEEPER!")
    # IMMEDIATE ACTION: SUBSCRIBE
    logger.info(f"Sending Subscription for {len(SUBSCRIPTION_PAYLOAD)} items...")
    sio.emit('subscribe', SUBSCRIPTION_PAYLOAD)

@sio.on('normalizedMessage')
def on_normalized(data):
    # This event usually contains Game Metadata (Teams, Scores, IDs)
    logger.info("RECEIVED: normalizedMessage (Game Data!)")
    captured_events.append({"type": "normalizedMessage", "data": data})

@sio.on('outcome-pricing-update')
def on_pricing(data):
    # This event contains the Odds
    # We log a snippet but don't fill the screen
    logger.info(f"RECEIVED: Pricing Update ({len(str(data))} bytes)")
    captured_events.append({"type": "outcome-pricing-update", "data": data})

@sio.on('*')
def catch_all(event, data):
    if event not in ['normalizedMessage', 'outcome-pricing-update']:
        logger.info(f"RECEIVED EVENT: {event}")
        captured_events.append({"type": event, "data": data})

def validate_keeper_data(events: list) -> bool:
    """Edge Data Integrity Check for Scorekeeper Events."""
    if not events:
        logger.error("Validation Failed: No events captured")
        return False
    # We expect at least some pricing updates or normalized messages
    pricing_count = sum(1 for e in events if e['type'] == 'outcome-pricing-update')
    if pricing_count == 0 and len(events) > 0:
        logger.warning("Validation Warning: No pricing updates received (might be off-hours)")
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Connecting to Scorekeeper...")
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
        
        if validate_keeper_data(captured_events):
            # Upload
            filename = f"scorekeeper_dump_{int(time.time())}.json"
            blob = bucket.blob(f"raw_data/{filename}")
            blob.upload_from_string(json.dumps(captured_events, default=str), content_type='application/json')
            
            logger.info(f"Data Secured: gs://{BUCKET_NAME}/raw_data/{filename}")
            sio.disconnect()
            
            # GENERATE EXECUTION REPORT
            report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_scorekeeper",
                change_summary="Scorekeeper Socket Capture",
                primary_metric="events_captured",
                metric_before=0.0,
                metric_after=float(len(captured_events)),
                observation_window_hours=0.01,
                success=True,
                notes=f"Secured: {len(captured_events)} events"
            )
            
            # UPLOAD REPORT
            timestamp = int(time.time())
            report_filename = f"report_scorekeeper_{timestamp}.json"
            blob_report = bucket.blob(f"governance/executions/{report_filename}")
            blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
            logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
            
            return True
        else:
            logger.warning("   -> Scorekeeper data validation failed.")
            sio.disconnect()
            return False
        
    except Exception as e:
        logger.error(f"Keeper Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_scorekeeper",
                change_summary="Scorekeeper Capture (FAILED)",
                primary_metric="events_captured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_scorekeeper_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_keeper",
        human_readable_name="Acquisitions Officer (Scorekeeper)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need real-time scores and odds",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
