import nfl_data_py as nfl
import pandas as pd
import json
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class NFLVerseWorker(BaseWorker):
    """
    Worker for importing NFL Play-by-Play data using nfl_data_py.
    """
    
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
            # nfl_data_py handles its own requests, so we can't easily inject self.session.
            # However, it's a library wrapper, so we trust it.
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
                return True
            else:
                self.logger.warning("   -> Dataframe validation failed.")
                return False
                
        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
