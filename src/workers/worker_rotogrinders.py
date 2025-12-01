import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class RotoGrindersWorker(BaseWorker):
    """
    Worker for scraping RotoGrinders weather data.
    """
    TARGET_URL = "https://rotogrinders.com/weather/mlb"

    def validate_html(self, content: bytes, name: str) -> bool:
        """Edge Data Integrity Check for HTML Content."""
        if not content:
            self.logger.error(f"Validation Failed: {name} is empty")
            return False
        if len(content) < 500: # Arbitrary small size check
            self.logger.warning(f"Validation Warning: {name} is suspiciously small ({len(content)} bytes)")
            return False
        return True

    def run(self) -> bool:
        self.logger.info("Checking the wind (RotoGrinders)...")
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                if self.validate_html(resp.content, "Weather Page"):
                    filename = f"rotogrinders_weather_{int(time.time())}.html"
                    # Use bucket directly for HTML
                    blob = self.bucket.blob(f"results/weather/{filename}")
                    blob.upload_from_string(resp.content, content_type='text/html')
                    self.logger.info(f"   -> Weather Report Secured (HTML).")
                    
                    # GENERATE EXECUTION REPORT
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem=self.__class__.__name__,
                        change_summary="MLB Weather Scrape",
                        primary_metric="bytes_secured",
                        metric_before=0.0,
                        metric_after=float(len(resp.content)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(resp.content)} bytes"
                    )
                    self.file_report(report)
                    return True
                else:
                    self.logger.warning("   -> HTML validation failed.")
                    return False
            else:
                self.logger.error(f"Scrape failed: {resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="MLB Weather Scrape (FAILED)",
                primary_metric="bytes_secured",
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
        agent_id="acquisitions_officer_roto",
        human_readable_name="Acquisitions Officer (RotoGrinders)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need weather risk assessment",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = RotoGrindersWorker(good_ctx)
    worker.execute(ctx=good_ctx)
