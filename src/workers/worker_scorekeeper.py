import socketio
import logging
import json
import time
import os
import sys

# IMPORT GOVERNANCE LAYERS
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
                return True
            else:
                self.logger.warning("   -> Scorekeeper data validation failed.")
                self.sio.disconnect()
                return False
            
        except Exception as e:
            self.logger.error(f"Keeper Failed: {e}")
            # Generate Failure Report
            return False
