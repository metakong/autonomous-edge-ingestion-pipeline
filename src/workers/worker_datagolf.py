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

class DataGolfWorker(BaseWorker):
    """
    Worker for scraping Data Golf rankings.
    """
    TARGET_URL = "https://datagolf.com/datagolf-rankings"

    def validate_dataframe(self, df: pd.DataFrame, name: str) -> bool:
        """Edge Data Integrity Check for DataFrames."""
        if df is None:
            self.logger.error(f"Validation Failed: {name} is None")
            return False
        if df.empty:
            self.logger.warning(f"Validation Warning: {name} is empty")
            return False
        return True

    def run(self) -> bool:
        self.logger.info("Teeing off (Data Golf)...")
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                # Data Golf renders tables via JS usually.
                # We will try to find the table in the static HTML first.
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Look for table
                table = soup.find('table')
                if table:
                    df = pd.read_html(str(table))[0]
                    
                    if self.validate_dataframe(df, "Rankings Table"):
                        filename = f"datagolf_rankings_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/golf/{filename}")
                        blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> Rankings Secured: {len(df)} golfers.")
                        
                        # GENERATE EXECUTION REPORT
                        report = ExecutionReport(
                            stage=DSIEStage.EXECUTE,
                            subsystem=self.__class__.__name__,
                            change_summary="Data Golf Rankings Scrape",
                            primary_metric="golfers_secured",
                            metric_before=0.0,
                            metric_after=float(len(df)),
                            observation_window_hours=0.01,
                            success=True,
                            notes=f"Secured: {len(df)} golfers"
                        )
                        self.file_report(report)
                        return True
                    else:
                        self.logger.warning("   -> Dataframe validation failed.")
                        return False
                else:
                    # If no table, save HTML for headless processing later
                    filename = f"datagolf_raw_{int(time.time())}.html"
                    blob = self.bucket.blob(f"results/golf/{filename}")
                    blob.upload_from_string(resp.content, content_type='text/html')
                    self.logger.info(f"   -> Raw HTML Secured (JS Rendering likely required).")
                    
                    # Report Partial Success
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem=self.__class__.__name__,
                        change_summary="Data Golf Raw HTML Scrape",
                        primary_metric="bytes_secured",
                        metric_before=0.0,
                        metric_after=float(len(resp.content)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {len(resp.content)} bytes (Raw HTML)"
                    )
                    self.file_report(report)
                    return True
            else:
                self.logger.error(f"Scrape failed: {resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="Data Golf Scrape (FAILED)",
                primary_metric="golfers_secured",
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
        agent_id="acquisitions_officer_golf",
        human_readable_name="Acquisitions Officer (Data Golf)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need true strokes gained data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = DataGolfWorker(good_ctx)
    worker.execute(ctx=good_ctx)
