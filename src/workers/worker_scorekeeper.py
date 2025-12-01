import socketio
import logging
import json
import time
import os
import sys

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class ScorekeeperWorker(BaseWorker):
    """
    Worker for SportTrade Scorekeeper via SocketIO.
    """
    URL = "https://scorekeeper.prod.east.sporttrade.app"
    
    # HARDCODED CONTEST IDS (Scraped from your previous logs)
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

    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.captured_events = []
        
        # Register callbacks
        self.sio.on('connect', self.on_connect)
        self.sio.on('normalizedMessage', self.on_normalized)
        self.sio.on('outcome-pricing-update', self.on_pricing)
        self.sio.on('*', self.catch_all)

    def on_connect(self):
        self.logger.info("CONNECTED to SCOREKEEPER!")
        # IMMEDIATE ACTION: SUBSCRIBE
        self.logger.info(f"Sending Subscription for {len(self.SUBSCRIPTION_PAYLOAD)} items...")
        self.sio.emit('subscribe', self.SUBSCRIPTION_PAYLOAD)

    def on_normalized(self, data):
        # This event usually contains Game Metadata (Teams, Scores, IDs)
        self.logger.info("RECEIVED: normalizedMessage (Game Data!)")
        self.captured_events.append({"type": "normalizedMessage", "data": data})

    def on_pricing(self, data):
        # This event contains the Odds
        self.logger.info(f"RECEIVED: Pricing Update ({len(str(data))} bytes)")
        self.captured_events.append({"type": "outcome-pricing-update", "data": data})

    def catch_all(self, event, data):
        if event not in ['normalizedMessage', 'outcome-pricing-update']:
            self.logger.info(f"RECEIVED EVENT: {event}")
            self.captured_events.append({"type": event, "data": data})

    def validate_keeper_data(self, events: list) -> bool:
        """Edge Data Integrity Check for Scorekeeper Events."""
        if not events:
            self.logger.error("Validation Failed: No events captured")
            return False
        # We expect at least some pricing updates or normalized messages
        pricing_count = sum(1 for e in events if e['type'] == 'outcome-pricing-update')
        if pricing_count == 0 and len(events) > 0:
            self.logger.warning("Validation Warning: No pricing updates received (might be off-hours)")
        return True

    def run(self) -> bool:
        self.logger.info("Connecting to Scorekeeper...")
        self.captured_events = [] # Reset buffer
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "Origin": "https://platform.getsporttrade.com"
        }
        
        try:
            self.sio.connect(self.URL, headers=headers, transports=['websocket'])
            
            # Listen for 15 seconds
            time.sleep(15)
            
            self.logger.info("Session complete. Uploading capture...")
            
            if self.validate_keeper_data(self.captured_events):
                # Upload
                filename = f"scorekeeper_dump_{int(time.time())}.json"
                blob = self.bucket.blob(f"raw_data/{filename}")
                blob.upload_from_string(json.dumps(self.captured_events, default=str), content_type='application/json')
                
                self.logger.info(f"Data Secured: gs://{self.config.BUCKET_NAME}/raw_data/{filename}")
                self.sio.disconnect()
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem=self.__class__.__name__,
                    change_summary="Scorekeeper Socket Capture",
                    primary_metric="events_captured",
                    metric_before=0.0,
                    metric_after=float(len(self.captured_events)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(self.captured_events)} events"
                )
                self.file_report(report)
                return True
            else:
                self.logger.warning("   -> Scorekeeper data validation failed.")
                self.sio.disconnect()
                return False
            
        except Exception as e:
            self.logger.error(f"Keeper Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="Scorekeeper Capture (FAILED)",
                primary_metric="events_captured",
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
    worker = ScorekeeperWorker(good_ctx)
    worker.execute(ctx=good_ctx)
