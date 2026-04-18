import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
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
                return True
            else:
                self.logger.warning("   -> No data found.")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
