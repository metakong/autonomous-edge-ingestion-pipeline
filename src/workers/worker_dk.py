import sys
import os
import time
import logging

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class DraftKingsWorker(BaseWorker):
    
    URL = "https://sportsbook-nash.draftkings.com/sites/US-IL-SB/api/sportscontent/controldata/league/leagueSubcategory/v1/markets"
    PARAMS = {
        "isBatchable": "false",
        "templateVars": "88808,4518",
        "eventsQuery": "$filter=leagueId eq '88808' AND clientMetadata/Subcategories/any(s: s/Id eq '4518')",
        "marketsQuery": "$filter=clientMetadata/subCategoryId eq '4518' AND tags/all(t: t ne 'SportcastBetBuilder')",
        "include": "Events",
        "entity": "events"
    }
    HEADERS = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://sportsbook.draftkings.com",
        "Referer": "https://sportsbook.draftkings.com/",
    }

    def validate_data(self, data: dict) -> bool:
        if not data:
            self.logger.error("Validation Failed: Empty response")
            return False
        
        events = data.get("events", [])
        if not isinstance(events, list):
            self.logger.error("Validation Failed: 'events' is not a list")
            return False
        
        if len(events) == 0:
            self.logger.warning("Validation Warning: No events found (Off-season?)")
            return True
            
        first_event = events[0]
        if "id" not in first_event or "name" not in first_event:
            self.logger.error(f"Validation Failed: Malformed event structure. Keys found: {list(first_event.keys())}")
            return False
            
        return True

    def run(self) -> bool:
        self.logger.info("Hitting DraftKings Nash API...")
        
        try:
            # Merge class headers with session headers (User-Agent is already in session)
            headers = self.session.headers.copy()
            headers.update(self.HEADERS)
            
            response = self.session.get(self.URL, headers=headers, params=self.PARAMS, timeout=self.config.DEFAULT_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                if not self.validate_data(data):
                    raise ValueError("Data failed integrity checks")
                
                events = data.get("events", [])
                self.logger.info(f"Found {len(events)} events.")
                
                # Upload Raw Data
                timestamp = int(time.time())
                filename = f"draftkings_nfl_{timestamp}.json"
                self.upload_json(data, f"results/draftkings/{filename}")
                
                # File Report
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem=self.__class__.__name__,
                    change_summary="Routine scrape run",
                    primary_metric="events_found",
                    metric_before=0.0,
                    metric_after=float(len(events)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Uploaded to {filename}"
                )
                self.file_report(report)
                return True
            else:
                self.logger.error(f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # File Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="Routine scrape run (FAILED)",
                primary_metric="events_found",
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
    logger = logging.getLogger("KajiDK")

    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_01",
        human_readable_name="Acquisitions Officer",
        autonomy_level=2
    )

    # TEST 1: RUN WITHOUT DIAGNOSIS (SHOULD FAIL)
    print("\n--- ATTEMPT 1: Running naked (No Diagnosis) ---")
    try:
        bad_ctx = AgentContext(contract=contract, current_diagnosis=None)
        worker = DraftKingsWorker(bad_ctx)
        worker.execute(ctx=bad_ctx)
    except Exception as e:
        logger.error(f"BLOCKED BY GOVERNANCE: {e}")

    # TEST 2: RUN WITH DIAGNOSIS (SHOULD SUCCEED)
    print("\n--- ATTEMPT 2: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need fresh NFL odds",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = DraftKingsWorker(good_ctx)
    worker.execute(ctx=good_ctx)
