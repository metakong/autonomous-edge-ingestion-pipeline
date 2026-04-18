import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class NFLPenaltiesWorker(BaseWorker):
    """
    Worker for scraping NFL penalties data.
    """
    TARGET_URL = "https://www.nflpenalties.com/all-positions.php?year=2024"

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
        self.logger.info("Flag on the play (NFLPenalties.com)...")
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            # BaseWorker session already has a User-Agent, but let's ensure it's robust if needed.
            # The original code had a specific UA. BaseWorker uses Config.USER_AGENT.
            # We'll stick with BaseWorker's session.
            
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # Find the main table
                table = soup.find('table', {'class': 'table'})
                if table:
                    # Parse with Pandas
                    df = pd.read_html(str(table))[0]
                    
                    if self.validate_dataframe(df, "Penalties Table"):
                        filename = f"nfl_penalties_2024_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/nfl/{filename}")
                        blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> Flags Secured: {len(df)} rows.")
                        
                        # GENERATE EXECUTION REPORT
                        return True
                    else:
                        self.logger.warning("   -> Dataframe validation failed.")
                        return False
                else:
                    self.logger.error("   -> Table not found in HTML.")
                    return False
            else:
                self.logger.error(f"Scrape failed: {resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
