import pandas as pd
import time
import os
import logging
import sys
from typing import Optional

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class TennisWorker(BaseWorker):
    """
    Worker for scraping ATP match data from Jeff Sackmann's GitHub.
    """
    REPO_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2024.csv"

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
        self.logger.info("Serving for the Match (Tennis Abstract)...")
        
        try:
            self.logger.info(f"Downloading 2024 ATP Match Data from {self.REPO_URL}...")
            
            # Pandas can read CSV directly from URL
            # Using self.session to get content first might be safer for timeouts/headers, 
            # but pandas read_csv is convenient. 
            # Let's use pandas directly as in original, but wrap in try-except block.
            try:
                df = pd.read_csv(self.REPO_URL)
            except Exception as e:
                self.logger.error(f"Failed to download CSV: {e}")
                raise e
            
            if self.validate_dataframe(df, "ATP Matches"):
                filename = f"atp_matches_2024_{int(time.time())}.csv"
                self.upload_json(df.to_csv(index=False), f"results/tennis/{filename}") # upload_json handles string content too if we pass string? No, upload_json dumps to json.
                # BaseWorker.upload_json dumps to json. We need to upload raw string/csv.
                # Let's use bucket directly for CSV.
                
                blob = self.bucket.blob(f"results/tennis/{filename}")
                blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                self.logger.info(f"Uploaded: gs://{self.config.BUCKET_NAME}/results/tennis/{filename}")
                
                self.logger.info(f"   -> Game, Set, Match: {len(df)} matches secured.")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem=self.__class__.__name__,
                    change_summary="ATP Match Data Scrape",
                    primary_metric="matches_secured",
                    metric_before=0.0,
                    metric_after=float(len(df)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(df)} matches"
                )
                self.file_report(report)
                return True
            else:
                self.logger.warning("   -> No data found (Fault?).")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="ATP Match Data Scrape (FAILED)",
                primary_metric="matches_secured",
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
        agent_id="acquisitions_officer_tennis",
        human_readable_name="Acquisitions Officer (Tennis)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need tennis match data for surface analysis",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = TennisWorker(good_ctx)
    worker.execute(ctx=good_ctx)
