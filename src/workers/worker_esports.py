import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from src.base_worker import BaseWorker

class EsportsWorker(BaseWorker):
    """
    Worker for scraping Esports data (LoL).
    """
    # Oracle's Elixir LoL Data (2024)
    CSV_URL = "https://oracleselixir-downloadable-match-data.s3-us-west-2.amazonaws.com/2024_LoL_esports_match_data_from_OraclesElixir.csv"

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
        self.logger.info("Entering Summoner's Rift (Oracle's Elixir)...")
        
        try:
            self.logger.info(f"Downloading 2024 LoL Match Data from {self.CSV_URL}...")
            
            # Read directly
            # Since it's a CSV URL, pandas can read it directly.
            # However, for robustness and to use our session (if needed for auth/headers, though S3 usually public),
            # we could download first. But read_csv is standard.
            # Let's stick to read_csv but wrap in try-except.
            
            df = pd.read_csv(self.CSV_URL)
            
            if self.validate_dataframe(df, "LoL Matches"):
                filename = f"lol_matches_2024_{int(time.time())}.csv"
                # Use bucket directly for CSV upload
                blob = self.bucket.blob(f"results/esports/{filename}")
                blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                self.logger.info(f"   -> Nexus Destroyed: {len(df)} rows secured.")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem=self.__class__.__name__,
                    change_summary="LoL Match Data Scrape",
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
                self.logger.warning("   -> No data found.")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="LoL Match Data Scrape (FAILED)",
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
        agent_id="acquisitions_officer_esports",
        human_readable_name="Acquisitions Officer (Esports)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need LoL match data for early game analysis",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = EsportsWorker(good_ctx)
    worker.execute(ctx=good_ctx)
