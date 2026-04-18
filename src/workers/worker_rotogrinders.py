import time

from src.base_worker import BaseWorker


class RotoGrindersWorker(BaseWorker):
    """
    Worker for scraping RotoGrinders weather data.
    """
    TARGET_URL = "https://rotogrinders.com/weather/mlb"

    def validate_html(self, content: bytes, name: str) -> bool:
        """Edge Data Integrity Check for raw HTML content."""
        if not content:
            self.logger.error(f"Validation Failed: {name} is empty")
            return False
        if len(content) < 500:
            self.logger.warning(
                f"Validation Warning: {name} is suspiciously small ({len(content)} bytes)"
            )
            return False
        return True

    def run(self) -> bool:
        self.logger.info("Checking the wind (RotoGrinders)...")

        try:
            self.logger.info(f"Scraping {self.TARGET_URL}...")
            resp = self.session.get(self.TARGET_URL, timeout=self.config.DEFAULT_TIMEOUT)

            if resp.status_code == 200:
                if self.validate_html(resp.content, "Weather Page"):
                    filename = f"rotogrinders_weather_{int(time.time())}.html"
                    blob = self.bucket.blob(f"results/weather/{filename}")
                    blob.upload_from_string(resp.content, content_type="text/html")
                    self.logger.info("   -> Weather Report Secured (HTML).")
                    return True
                else:
                    self.logger.warning("   -> HTML validation failed.")
                    return False
            else:
                self.logger.error(f"Scrape failed: {resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            return False
