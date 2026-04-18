import pybaseball
import pandas as pd
import json
import time
import os
import logging
import sys
from datetime import datetime, timedelta

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class BaseballWorker(BaseWorker):
    
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
        self.logger.info("Initiating Triple Play (Savant, FanGraphs, BRef)...")
        items_secured = []
        
        try:
            # 1. BASEBALL SAVANT (Statcast)
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            self.logger.info(f"1. Pitching to Baseball Savant for {yesterday}...")
            
            try:
                df_savant = pybaseball.statcast(start_dt=yesterday, end_dt=yesterday)
                if self.validate_dataframe(df_savant, "Savant Data"):
                    savant_file = f"savant_statcast_{yesterday}_{int(time.time())}.csv"
                    blob = self.bucket.blob(f"results/baseball/{savant_file}")
                    blob.upload_from_string(df_savant.to_csv(index=False), content_type='text/csv')
                    self.logger.info(f"   -> Savant Secured: {len(df_savant)} pitches.")
                    items_secured.append(f"Savant ({len(df_savant)} rows)")
            except Exception as e:
                self.logger.error(f"   -> Savant Error: {e}")

            # 2. FANGRAPHS (Batting Leaders)
            self.logger.info("2. Swinging for FanGraphs (2024 Batting Leaders)...")
            try:
                df_fg = pybaseball.batting_stats(2024)
                if self.validate_dataframe(df_fg, "FanGraphs Data"):
                    fg_file = f"fangraphs_batting_2024_{int(time.time())}.csv"
                    blob = self.bucket.blob(f"results/baseball/{fg_file}")
                    blob.upload_from_string(df_fg.to_csv(index=False), content_type='text/csv')
                    self.logger.info(f"   -> FanGraphs Secured: {len(df_fg)} players.")
                    items_secured.append(f"FanGraphs ({len(df_fg)} rows)")
            except Exception as e:
                self.logger.error(f"   -> FanGraphs Error: {e}")

            # 3. BASEBALL REFERENCE (Team Standings)
            self.logger.info("3. Rounding third with Baseball Reference (2024 Standings)...")
            try:
                standings_list = pybaseball.standings(2024)
                if standings_list:
                    df_bref = pd.concat(standings_list)
                    if self.validate_dataframe(df_bref, "BRef Data"):
                        bref_file = f"bref_standings_2024_{int(time.time())}.csv"
                        blob = self.bucket.blob(f"results/baseball/{bref_file}")
                        blob.upload_from_string(df_bref.to_csv(index=False), content_type='text/csv')
                        self.logger.info(f"   -> BRef Secured: {len(df_bref)} teams.")
                        items_secured.append(f"BRef ({len(df_bref)} rows)")
                else:
                    self.logger.warning("   -> BRef returned no data.")
            except Exception as e:
                self.logger.error(f"   -> BRef Error: {e}")

            # GENERATE EXECUTION REPORT
            success = len(items_secured) > 0
            return success

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
