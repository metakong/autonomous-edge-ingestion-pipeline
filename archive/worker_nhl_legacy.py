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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-NHL] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiNHL")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# NHL API ENDPOINTS (Unofficial but public)
SCHEDULE_URL = "https://api-web.nhle.com/v1/schedule/now"

def validate_schedule(data: dict) -> bool:
    """Edge Data Integrity Check for NHL Schedule."""
    if not data:
        logger.error("Validation Failed: Empty response")
        return False
    if "gameWeek" not in data:
        logger.error("Validation Failed: 'gameWeek' key missing")
        return False
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Skating towards NHL API...")
    start_time = time.time()
    items_secured = []
    
    try:
        # 1. GET SCHEDULE (Current Week)
        logger.info(f"Fetching current schedule from {SCHEDULE_URL}...")
        resp = requests.get(SCHEDULE_URL, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if validate_schedule(data):
                game_week = data.get("gameWeek", [])
                logger.info(f"Found {len(game_week)} days of games.")
                items_secured.append(f"Schedule ({len(game_week)} days)")
                
                # Save Schedule
                filename = f"nhl_schedule_{int(time.time())}.json"
                blob = bucket.blob(f"results/nhl/{filename}")
                blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
                logger.info(f"   -> Schedule Secured.")
                
                # 2. GET LIVE DATA FOR FIRST GAME (If available)
                if game_week:
                    first_day = game_week[0]
                    games = first_day.get("games", [])
                    if games:
                        game_id = games[0]["id"]
                        # GameCenter Endpoint
                        game_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
                        logger.info(f"Fetching Boxscore for Game ID {game_id}...")
                        
                        try:
                            game_resp = requests.get(game_url, timeout=10)
                            if game_resp.status_code == 200:
                                game_data = game_resp.json()
                                if "id" in game_data: # Basic check
                                    game_file = f"nhl_game_{game_id}_{int(time.time())}.json"
                                    blob = bucket.blob(f"results/nhl/{game_file}")
                                    blob.upload_from_string(json.dumps(game_data, indent=2), content_type='application/json')
                                    logger.info(f"   -> Boxscore Secured.")
                                    items_secured.append(f"Boxscore ({game_id})")
                                else:
                                    logger.warning("   -> Boxscore validation failed.")
                            else:
                                logger.warning(f"   -> Boxscore failed: {game_resp.status_code}")
                        except Exception as e:
                            logger.error(f"   -> Boxscore Error: {e}")
            
            # GENERATE EXECUTION REPORT
            report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_nhl",
                change_summary="NHL Schedule & Boxscore Scrape",
                primary_metric="items_secured",
                metric_before=0.0,
                metric_after=float(len(items_secured)),
                observation_window_hours=0.01,
                success=True,
                notes=f"Secured: {', '.join(items_secured)}"
            )
            
            # UPLOAD REPORT
            timestamp = int(time.time())
            report_filename = f"report_nhl_{timestamp}.json"
            blob_report = bucket.blob(f"governance/executions/{report_filename}")
            blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
            logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
            
            return True
        else:
            logger.error(f"Schedule failed: {resp.status_code}")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_nhl",
                change_summary="NHL Schedule Scrape (FAILED)",
                primary_metric="items_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_nhl_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_nhl",
        human_readable_name="Acquisitions Officer (NHL)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need NHL schedule and boxscore data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
