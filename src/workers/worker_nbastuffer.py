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

class NBAStufferWorker(BaseWorker):
    """
    Worker for scraping NBA rest stats from NBAStuffer.
    """
    TARGET_URL = "https://www.nbastuffer.com/2024-2025-nba-rest-days-stats/"

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
        self.logger.info("Checking the injury report (NBAStuffer)...")
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Find tables
                tables = pd.read_html(str(soup))
                if tables:
                    # Usually the first table is the main one
                    df = tables[0]
                    
                    if self.validate_dataframe(df, "Rest Stats"):
                        filename = f"nba_rest_stats_2025_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/nba/{filename}")
                        blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> Rest Stats Secured: {len(df)} rows.")
                        
                        # GENERATE EXECUTION REPORT
                        report = ExecutionReport(
                            stage=DSIEStage.EXECUTE,
                            subsystem=self.__class__.__name__,
                            change_summary="NBA Rest Stats Scrape",
                            primary_metric="rows_secured",
                            metric_before=0.0,
                            metric_after=float(len(df)),
                            observation_window_hours=0.01,
                            success=True,
                            notes=f"Secured: {len(df)} rows"
                        )
                        self.file_report(report)
                        return True
                    else:
                        self.logger.warning("   -> Dataframe validation failed.")
                        return False
                else:
                    self.logger.error("   -> No tables found.")
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
                change_summary="NBA Rest Stats Scrape (FAILED)",
                primary_metric="rows_secured",
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
        agent_id="acquisitions_officer_nbastuffer",
        human_readable_name="Acquisitions Officer (NBA Stuffer)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need schedule fatigue analysis",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = NBAStufferWorker(good_ctx)
    worker.execute(ctx=good_ctx)
