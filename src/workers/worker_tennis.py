import pandas as pd
import time

from src.base_worker import BaseWorker


class TennisWorker(BaseWorker):
    """
    Worker for scraping ATP match data from Jeff Sackmann's public GitHub repository.
    Zero-friction ingestion — no authentication required.
    """
    REPO_URL = (
        "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/"
        "atp_matches_2024.csv"
    )

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
            df = pd.read_csv(self.REPO_URL)

            if self.validate_dataframe(df, "ATP Matches"):
                filename = f"atp_matches_2024_{int(time.time())}.csv"
                blob = self.bucket.blob(f"results/tennis/{filename}")
                blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
                self.logger.info(
                    f"Uploaded: gs://{self.config.BUCKET_NAME}/results/tennis/{filename}"
                )
                self.logger.info(f"   -> Game, Set, Match: {len(df)} matches secured.")
                return True
            else:
                self.logger.warning("   -> No data found (Fault?).")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            return False
