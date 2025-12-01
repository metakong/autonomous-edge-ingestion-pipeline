import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class FBRefWorker(BaseWorker):
    """
    Worker for scraping FBref (Soccer) data.
    """
    TARGET_URL = "https://fbref.com/en/comps/9/Premier-League-Stats"

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
        self.logger.info("Checking VAR (FBref)...")
        items_secured = []
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            
            # Use self.session to fetch content, ensuring headers/proxies are used.
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                # Pass content to pd.read_html
                dfs = pd.read_html(resp.content)
                
                if dfs:
                    # Usually the first table is the standings
                    standings = dfs[0]
                    if self.validate_dataframe(standings, "Standings"):
                        filename = f"fbref_pl_standings_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/soccer/{filename}")
                        blob.upload_from_string(standings.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> Standings Secured: {len(standings)} teams.")
                        items_secured.append(f"Standings ({len(standings)} rows)")
                    
                    # Often there are more tables (Squad Stats, etc)
                    if len(dfs) > 1:
                        stats = dfs[1] # Hypothetical
                        if self.validate_dataframe(stats, "Squad Stats"):
                            filename_stats = f"fbref_pl_stats_{int(time.time())}.csv"
                            blob_stats = self.bucket.blob(f"results/soccer/{filename_stats}")
                            blob_stats.upload_from_string(stats.to_csv(index=False), content_type='text/csv')
                            self.logger.info(f"   -> Squad Stats Secured.")
                            items_secured.append(f"Squad Stats ({len(stats)} rows)")
                    
                    # GENERATE EXECUTION REPORT
                    report = ExecutionReport(
                        stage=DSIEStage.EXECUTE,
                        subsystem=self.__class__.__name__,
                        change_summary="FBref PL Stats Scrape",
                        primary_metric="tables_secured",
                        metric_before=0.0,
                        metric_after=float(len(items_secured)),
                        observation_window_hours=0.01,
                        success=True,
                        notes=f"Secured: {', '.join(items_secured)}"
                    )
                    self.file_report(report)
                    return True
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
                change_summary="FBref Scrape (FAILED)",
                primary_metric="tables_secured",
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
        agent_id="acquisitions_officer_fbref",
        human_readable_name="Acquisitions Officer (FBref)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need soccer xG data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = FBRefWorker(good_ctx)
    worker.execute(ctx=good_ctx)
