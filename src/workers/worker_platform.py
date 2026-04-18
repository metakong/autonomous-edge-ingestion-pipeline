import socketio
import logging
import json
import time
import os
import sys

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class PlatformWorker(BaseWorker):
    """
    Worker for SportTrade Platform via SocketIO.
    """
    URL = "https://platform.getsporttrade.com"
    
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

    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.captured_events = []
        
        # Register callbacks
        self.sio.on('connect', self.on_connect)
        self.sio.on('*', self.catch_all)

    def on_connect(self):
        self.logger.info("CONNECTED to PLATFORM!")
        # THE KEY STEP: Ask for the data
        self.logger.info(f"Sending Subscription...")
        self.sio.emit('subscribe', self.SUBSCRIPTION_PAYLOAD)

    def catch_all(self, event, data):
        self.logger.info(f"RECEIVED EVENT: {event}")
        
        # Check for the Rosetta Stone
        text_dump = json.dumps(data)
        if "Buffalo" in text_dump or "Steelers" in text_dump:
            self.logger.info(">>> TARGET ACQUIRED (Names Found!) <<<")
        
        self.captured_events.append({"type": event, "data": data})

    def validate_platform_data(self, events: list) -> bool:
        """Edge Data Integrity Check for Platform Events."""
        if not events:
            self.logger.error("Validation Failed: No events captured")
            return False
        if len(events) < 5: # Arbitrary minimum
            self.logger.warning(f"Validation Warning: Low event count ({len(events)})")
            # Still return True as it might be a quiet time
        return True

    def run(self) -> bool:
        self.logger.info("Connecting to Platform...")
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
            
            if self.validate_platform_data(self.captured_events):
                filename = f"platform_dump_{int(time.time())}.json"
                blob = self.bucket.blob(f"raw_data/{filename}")
                blob.upload_from_string(json.dumps(self.captured_events, default=str), content_type='application/json')
                
                self.logger.info(f"Data Secured: gs://{self.config.BUCKET_NAME}/raw_data/{filename}")
                self.sio.disconnect()
                
                # GENERATE EXECUTION REPORT
                return True
            else:
                self.logger.warning("   -> Platform data validation failed.")
                self.sio.disconnect()
                return False
                
        except Exception as e:
            self.logger.error(f"Platform Failed: {e}")
            # Generate Failure Report
            return False
