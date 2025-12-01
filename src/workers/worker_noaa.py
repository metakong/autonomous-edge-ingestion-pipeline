import requests
import json
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class NOAAWorker(BaseWorker):
    """
    Worker for scraping NOAA weather data.
    """
    # NOAA API (Weather.gov)
    # User-Agent is REQUIRED by NOAA
    NOAA_HEADERS = {
        "User-Agent": "(veiled-vector-core, deardorff.sean@gmail.com)",
        "Accept": "application/geo+json"
    }

    # Target: Arrowhead Stadium (Kansas City)
    LAT = "39.0489"
    LON = "-94.4839"

    def validate_forecast(self, data: dict) -> bool:
        """Edge Data Integrity Check for NOAA Forecast."""
        if not data:
            self.logger.error("Validation Failed: Empty response")
            return False
        if "properties" not in data:
            self.logger.error("Validation Failed: 'properties' key missing")
            return False
        if "periods" not in data["properties"]:
            self.logger.error("Validation Failed: 'periods' key missing in properties")
            return False
        return True

    def run(self) -> bool:
        self.logger.info("Contacting National Weather Service...")
        
        try:
            # Merge headers
            headers = self.session.headers.copy()
            headers.update(self.NOAA_HEADERS)

            # Step 1: Get Grid Point
            points_url = f"https://api.weather.gov/points/{self.LAT},{self.LON}"
            self.logger.info(f"Resolving grid for {self.LAT}, {self.LON}...")
            
            resp = self.session.get(points_url, headers=headers, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code != 200:
                self.logger.error(f"Grid resolution failed: {resp.status_code} - {resp.text}")
                return False
                
            grid_data = resp.json()
            forecast_url = grid_data["properties"]["forecast"]
            
            # Step 2: Get Forecast
            self.logger.info(f"Fetching forecast from {forecast_url}...")
            forecast_resp = self.session.get(forecast_url, headers=headers, timeout=self.config.DEFAULT_TIMEOUT)
            
            if forecast_resp.status_code == 200:
                data = forecast_resp.json()
                
                if self.validate_forecast(data):
                    periods = data["properties"]["periods"]
                    self.logger.info(f"Retrieved {len(periods)} forecast periods.")
                    
                    filename = f"noaa_arrowhead_{int(time.time())}.json"
                    self.upload_json(data, f"results/weather/{filename}")
                    
                    self.logger.info(f"LOOT SECURED: gs://{self.config.BUCKET_NAME}/results/weather/{filename}")
                    
                    # GENERATE EXECUTION REPORT
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem=self.__class__.__name__,
                        change_summary="NOAA Forecast Scrape",
                        primary_metric="periods_secured",
                        metric_before=0.0,
                        metric_after=float(len(periods)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(periods)} forecast periods"
                    )
                    self.file_report(report)
                    return True
                else:
                    self.logger.warning("   -> Forecast validation failed.")
                    return False
            else:
                self.logger.error(f"Forecast failed: {forecast_resp.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="NOAA Forecast Scrape (FAILED)",
                primary_metric="periods_secured",
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
        agent_id="acquisitions_officer_noaa",
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
    worker = NOAAWorker(good_ctx)
    worker.execute(ctx=good_ctx)
