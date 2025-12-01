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

class UFCWorker(BaseWorker):
    """
    Worker for scraping UFC stats.
    """
    TARGET_URL = "http://ufcstats.com/statistics/events/completed"

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
        self.logger.info("Entering the Octagon (UFCStats)...")
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            
            # Use self.session for requests
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # The table is usually identifiable
                table = soup.find('table', {'class': 'b-statistics__table-events'})
                if table:
                    # Pandas read_html is powerful
                    df = pd.read_html(str(table))[0]
                    
                    # Cleanup: Remove rows that are just headers repeated or empty
                    df = df.dropna(how='all')
                    
                    if self.validate_dataframe(df, "UFC Events"):
                        filename = f"ufc_events_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/ufc/{filename}")
                        blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> Fight Card Secured: {len(df)} events.")
                        
                        # GENERATE EXECUTION REPORT
                        report = ExecutionReport(
                            stage=DSIEStage.EXECUTE,
                            subsystem=self.__class__.__name__,
                            change_summary="UFC Events Scrape",
                            primary_metric="events_secured",
                            metric_before=0.0,
                            metric_after=float(len(df)),
                            observation_window_hours=0.01,
                            success=True,
                            notes=f"Secured: {len(df)} events"
                        )
                        self.file_report(report)
                        return True
                    else:
                        self.logger.warning("   -> Dataframe validation failed.")
                        return False
                else:
                    self.logger.error("   -> Event table not found.")
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
                change_summary="UFC Events Scrape (FAILED)",
                primary_metric="events_secured",
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
        agent_id="acquisitions_officer_ufc",
        human_readable_name="Acquisitions Officer (UFC)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need historical fight results",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = UFCWorker(good_ctx)
    worker.execute(ctx=good_ctx)
