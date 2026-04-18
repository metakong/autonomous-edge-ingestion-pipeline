import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class SICWorker(BaseWorker):
    """
    Worker for scraping SIC Score (Sports Injury Central).
    """
    TARGET_URL = "https://sicscore.com/nfl/updates"

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
        self.logger.info("Checking the medical tent (SIC Score)...")
        
        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                
                # SIC Score usually has cards or a list of updates.
                # We will grab the text content of updates.
                
                articles = soup.find_all('article')
                data = []
                for article in articles:
                    text = article.get_text(strip=True)
                    data.append({"content": text})
                
                if data:
                    df = pd.DataFrame(data)
                    
                    if self.validate_dataframe(df, "SIC Updates"):
                        filename = f"sic_updates_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/injuries/{filename}")
                        blob.upload_from_string(df.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> Injury Reports Secured: {len(df)} updates.")
                        
                        # GENERATE EXECUTION REPORT
                        return True
                    else:
                        self.logger.warning("   -> Dataframe validation failed.")
                        return False
                else:
                    # Fallback: Save HTML if no articles found (site structure might differ)
                    filename = f"sic_raw_{int(time.time())}.html"
                    blob = self.bucket.blob(f"results/injuries/{filename}")
                    blob.upload_from_string(resp.content, content_type='text/html')
                    self.logger.info(f"   -> Raw HTML Secured (Structure uncertain).")
                    
                    # Report Partial Success
                    return True
            else:
                self.logger.error(f"Scrape failed: {resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
