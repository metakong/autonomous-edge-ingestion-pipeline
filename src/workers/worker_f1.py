import fastf1
import pandas as pd
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class F1Worker(BaseWorker):
    
    def __init__(self, ctx: AgentContext):
        super().__init__(ctx)
        # CACHE SETUP
        self.CACHE_DIR = "fastf1_cache"
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
        fastf1.Cache.enable_cache(self.CACHE_DIR)

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
        self.logger.info("Entering the Paddock (FastF1)...")
        items_secured = []
        
        try:
            # Target: 2024 Bahrain Grand Prix (Season Opener)
            YEAR = 2024
            RACE = "Bahrain"
            SESSION = "R" # Race
            
            self.logger.info(f"Loading session: {YEAR} {RACE} - {SESSION}...")
            session = fastf1.get_session(YEAR, RACE, SESSION)
            session.load()
            
            # 1. LAP TIMES
            self.logger.info("Extracting Lap Times...")
            laps = session.laps
            if self.validate_dataframe(laps, "Lap Times"):
                laps_file = f"f1_{YEAR}_{RACE}_laps_{int(time.time())}.csv"
                blob = self.bucket.blob(f"results/f1/{laps_file}")
                blob.upload_from_string(laps.to_csv(index=False), content_type='text/csv')
                self.logger.info(f"   -> Laps Secured: {len(laps)} laps.")
                items_secured.append(f"Laps ({len(laps)} rows)")
            
            # 2. TELEMETRY (Fastest Lap)
            self.logger.info("Extracting Telemetry for Fastest Lap...")
            try:
                fastest_lap = laps.pick_fastest()
                telemetry = fastest_lap.get_telemetry()
                if self.validate_dataframe(telemetry, "Telemetry"):
                    telemetry_file = f"f1_{YEAR}_{RACE}_fastest_lap_telemetry_{int(time.time())}.csv"
                    blob = self.bucket.blob(f"results/f1/{telemetry_file}")
                    blob.upload_from_string(telemetry.to_csv(index=False), content_type='text/csv')
                    self.logger.info(f"   -> Telemetry Secured: {len(telemetry)} data points.")
                    items_secured.append(f"Telemetry ({len(telemetry)} rows)")
            except Exception as e:
                self.logger.error(f"   -> Telemetry Error: {e}")

            # GENERATE EXECUTION REPORT
            success = len(items_secured) > 0
            return success

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
