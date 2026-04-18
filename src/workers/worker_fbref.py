import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
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
            return False
