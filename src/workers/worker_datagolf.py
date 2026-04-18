from bs4 import BeautifulSoup
import pandas as pd
import time

from src.base_worker import BaseWorker


class DataGolfWorker(BaseWorker):
    """
    Worker for scraping Data Golf player rankings.
    Note: Data Golf renders its tables via JavaScript.  When the static HTML
    contains a <table> we parse it directly.  If no table is found (JS-only
    render) we store the raw HTML for later headless processing.
    """
    TARGET_URL = "https://datagolf.com/datagolf-rankings"

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
        self.logger.info("Teeing off (Data Golf)...")

        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)

            if resp.status_code != 200:
                self.logger.error(f"Scrape failed: {resp.status_code}")
                return False

            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table")

            if table:
                df = pd.read_html(str(table))[0]

                if self.validate_dataframe(df, "Rankings Table"):
                    filename = f"datagolf_rankings_{int(time.time())}.csv"
                    blob = self.bucket.blob(f"results/golf/{filename}")
                    blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
                    self.logger.info(f"   -> Rankings Secured: {len(df)} golfers.")
                    return True
                else:
                    self.logger.warning("   -> Dataframe validation failed.")
                    return False
            else:
                # JS-rendered page — store raw HTML for headless processing
                filename = f"datagolf_raw_{int(time.time())}.html"
                blob = self.bucket.blob(f"results/golf/{filename}")
                blob.upload_from_string(resp.content, content_type="text/html")
                self.logger.info("   -> Raw HTML Secured (JS Rendering required).")
                return True

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            return False
