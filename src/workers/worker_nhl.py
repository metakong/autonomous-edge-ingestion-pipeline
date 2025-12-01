import requests
import json
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class NHLWorker(BaseWorker):
    """
    Worker for scraping NHL schedule and boxscore data.
    """
    SCHEDULE_URL = "https://api-web.nhle.com/v1/schedule/now"

    def validate_schedule(self, data: dict) -> bool:
        """Edge Data Integrity Check for NHL Schedule."""
        if not data:
            self.logger.error("Validation Failed: Empty response")
            return False
        if "gameWeek" not in data:
            self.logger.error("Validation Failed: 'gameWeek' key missing")
            return False
        return True

    def run(self) -> bool:
        self.logger.info("Skating towards NHL API...")
        items_secured = []
        
        try:
            # 1. GET SCHEDULE (Current Week)
            self.logger.info(f"Fetching current schedule from {self.SCHEDULE_URL}...")
            resp = self.session.get(self.SCHEDULE_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                data = resp.json()
                
                if self.validate_schedule(data):
                    game_week = data.get("gameWeek", [])
                    self.logger.info(f"Found {len(game_week)} days of games.")
                    items_secured.append(f"Schedule ({len(game_week)} days)")
                    
                    # Save Schedule
                    filename = f"nhl_schedule_{int(time.time())}.json"
                    self.upload_json(data, f"results/nhl/{filename}")
                    self.logger.info(f"   -> Schedule Secured.")
                    
                    # 2. GET LIVE DATA FOR FIRST GAME (If available)
                    if game_week:
                        first_day = game_week[0]
                        games = first_day.get("games", [])
                        if games:
                            game_id = games[0]["id"]
                            # GameCenter Endpoint
                            game_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
                            self.logger.info(f"Fetching Boxscore for Game ID {game_id}...")
                            
                            try:
                                game_resp = self.session.get(game_url, timeout=self.config.DEFAULT_TIMEOUT)
                                if game_resp.status_code == 200:
                                    game_data = game_resp.json()
                                    if "id" in game_data: # Basic check
                                        game_file = f"nhl_game_{game_id}_{int(time.time())}.json"
                                        self.upload_json(game_data, f"results/nhl/{game_file}")
                                        self.logger.info(f"   -> Boxscore Secured.")
                                        items_secured.append(f"Boxscore ({game_id})")
                                    else:
                                        self.logger.warning("   -> Boxscore validation failed.")
                                else:
                                    self.logger.warning(f"   -> Boxscore failed: {game_resp.status_code}")
                            except Exception as e:
                                self.logger.error(f"   -> Boxscore Error: {e}")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem=self.__class__.__name__,
                    change_summary="NHL Schedule & Boxscore Scrape",
                    primary_metric="items_secured",
                    metric_before=0.0,
                    metric_after=float(len(items_secured)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {', '.join(items_secured)}"
                )
                self.file_report(report)
                return True
            else:
                self.logger.error(f"Schedule failed: {resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="NHL Schedule Scrape (FAILED)",
                primary_metric="items_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            self.file_report(fail_report)
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
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
    worker = NHLWorker(good_ctx)
    worker.execute(ctx=good_ctx)
