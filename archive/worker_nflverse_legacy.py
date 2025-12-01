import nfl_data_py as nfl
import pandas as pd
import json
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
from base_worker import BaseWorker

class NFLVerseWorker(BaseWorker):
    
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
        self.logger.info("Importing NFL Play-by-Play Data...")
        
        try:
            # Import 2024 data
            self.logger.info("Downloading 2024 Play-by-Play data (this may take a moment)...")
            df = nfl.import_pbp_data([2024])
            
            if self.validate_dataframe(df, "NFL PBP Data"):
                self.logger.info(f"Downloaded {len(df)} rows of play-by-play data.")
                
                # Save to CSV string
                csv_data = df.to_csv(index=False)
                
                timestamp = int(time.time())
                filename = f"nflverse_pbp_2024_{timestamp}.csv"
                blob = self.bucket.blob(f"results/{filename}")
                blob.upload_from_string(csv_data, content_type='text/csv')
                
                self.logger.info(f"LOOT SECURED: gs://{self.config.BUCKET_NAME}/results/{filename}")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_nflverse",
                    change_summary="NFLVerse PBP Import",
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
                
        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_nflverse",
                change_summary="NFLVerse PBP Import (FAILED)",
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
    logger = logging.getLogger("KajiNFLVerse")

    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_02",
        human_readable_name="Acquisitions Officer (NFLVerse)",
        autonomy_level=2
    )

    # TEST 1: RUN WITHOUT DIAGNOSIS (SHOULD FAIL)
    print("\n--- ATTEMPT 1: Running naked (No Diagnosis) ---")
    try:
        bad_ctx = AgentContext(contract=contract, current_diagnosis=None)
        worker = NFLVerseWorker(bad_ctx)
        worker.execute(ctx=bad_ctx)
    except Exception as e:
        logger.error(f"BLOCKED BY GOVERNANCE: {e}")

    # TEST 2: RUN WITH DIAGNOSIS (SHOULD SUCCEED)
    print("\n--- ATTEMPT 2: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need baseline NFL play-by-play data",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = NFLVerseWorker(good_ctx)
    worker.execute(ctx=good_ctx)
