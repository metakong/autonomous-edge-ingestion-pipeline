from src.base_worker import BaseWorker


class ChickenStatsWorker(BaseWorker):
    """
    Worker for ChickenStats (Evolving Hockey placeholder).

    NOTE: The chickenstats library processes local CSV files exported from
    Evolving Hockey, which requires an active paid subscription.  This worker
    acts as a readiness gate — it succeeds immediately and logs that the files
    must be manually placed before real processing can occur.  Once the CSVs
    are present they can be parsed via chickenstats.prep_pbp() and
    chickenstats.prep_stats().
    """

    def run(self) -> bool:
        self.logger.info("Faceoff (Evolving Hockey via ChickenStats)...")
        self.logger.warning(
            "ChickenStats processes local CSVs from an Evolving Hockey paid subscription."
        )
        self.logger.info(
            "   -> Drop the exported CSV files into the working directory, "
            "then re-run this worker to trigger real ingestion."
        )
        self.logger.info("   -> Marking as 'Ready for Ingestion'.")
        return True
