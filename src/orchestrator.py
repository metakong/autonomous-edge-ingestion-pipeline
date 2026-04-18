import time
import logging
import os
import sys
import importlib
import json
from typing import Dict, Any, Optional
from google.cloud import firestore
from google.cloud import storage

# Add project root to path to ensure imports work
# sys.path.append(os.getcwd())
# sys.path.append(os.path.join(os.getcwd(), "src"))

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ORCHESTRATOR] - %(levelname)s - %(message)s')
logger = logging.getLogger("Orchestrator")

# CONFIG
from src.config import Config

# Auth: Config handles this via Config.PROJECT_ID and Config.BUCKET_NAME
# We rely on ADC or GOOGLE_APPLICATION_CREDENTIALS being set externally.

# WORKER MAPPING
# Maps mission_type to (module_name, class_name, agent_id, human_name)
WORKER_REGISTRY = {
    "scrape_dk": ("src.workers.worker_dk", "DraftKingsWorker", "acquisitions_officer_dk", "Acquisitions Officer (DraftKings)"),
    "scrape_baseball": ("src.workers.worker_baseball", "BaseballWorker", "acquisitions_officer_baseball", "Acquisitions Officer (Baseball)"),
    "scrape_f1": ("src.workers.worker_f1", "F1Worker", "acquisitions_officer_f1", "Acquisitions Officer (F1)"),
    "scrape_tennis": ("src.workers.worker_tennis", "TennisWorker", "acquisitions_officer_tennis", "Acquisitions Officer (Tennis)"),
    "scrape_nhl": ("src.workers.worker_nhl", "NHLWorker", "acquisitions_officer_nhl", "Acquisitions Officer (NHL)"),
    "scrape_nflpenalties": ("src.workers.worker_nflpenalties", "NFLPenaltiesWorker", "acquisitions_officer_nflpenalties", "Acquisitions Officer (NFL Penalties)"),
    "scrape_nbastuffer": ("src.workers.worker_nbastuffer", "NBAStufferWorker", "acquisitions_officer_nbastuffer", "Acquisitions Officer (NBA Stuffer)"),
    "scrape_ufc": ("src.workers.worker_ufc", "UFCWorker", "acquisitions_officer_ufc", "Acquisitions Officer (UFC)"),
    "scrape_esports": ("src.workers.worker_esports", "EsportsWorker", "acquisitions_officer_esports", "Acquisitions Officer (Esports)"),
    "scrape_chickenstats": ("src.workers.worker_chickenstats", "ChickenStatsWorker", "acquisitions_officer_chickenstats", "Acquisitions Officer (ChickenStats)"),
    "scrape_rotogrinders": ("src.workers.worker_rotogrinders", "RotoGrindersWorker", "acquisitions_officer_rotogrinders", "Acquisitions Officer (RotoGrinders)"),
    "scrape_datagolf": ("src.workers.worker_datagolf", "DataGolfWorker", "acquisitions_officer_datagolf", "Acquisitions Officer (Data Golf)"),
    "scrape_fbref": ("src.workers.worker_fbref", "FBRefWorker", "acquisitions_officer_fbref", "Acquisitions Officer (FBref)"),
    "scrape_fd": ("src.workers.worker_fd", "FanDuelWorker", "acquisitions_officer_fd", "Acquisitions Officer (FanDuel)"),
    "scrape_nflverse": ("src.workers.worker_nflverse", "NFLVerseWorker", "acquisitions_officer_nflverse", "Acquisitions Officer (NFLVerse)"),
    "scrape_noaa": ("src.workers.worker_noaa", "NOAAWorker", "acquisitions_officer_noaa", "Acquisitions Officer (NOAA)"),
    "scrape_pp": ("src.workers.worker_pp", "PrizePicksWorker", "acquisitions_officer_pp", "Acquisitions Officer (PrizePicks)"),
    "scrape_sec": ("src.workers.worker_sec", "SECWorker", "acquisitions_officer_sec", "Acquisitions Officer (SEC)"),
    "scrape_sic": ("src.workers.worker_sic", "SICWorker", "acquisitions_officer_sic", "Acquisitions Officer (SIC Score)"),
    "scrape_umps": ("src.workers.worker_umps", "UmpsWorker", "acquisitions_officer_umps", "Acquisitions Officer (Umpire Scorecards)"),
    "scrape_platform": ("src.workers.worker_platform", "PlatformWorker", "acquisitions_officer_platform", "Acquisitions Officer (SportTrade Platform)"),
    "scrape_scorekeeper": ("src.workers.worker_scorekeeper", "ScorekeeperWorker", "acquisitions_officer_scorekeeper", "Acquisitions Officer (SportTrade Scorekeeper)"),
    "scrape_graphql": ("src.workers.worker_graphql", "GraphQLWorker", "acquisitions_officer_graphql", "Acquisitions Officer (GraphQL)"),
}

class Orchestrator:
    def __init__(self):
        # Explicitly connect to the named database, not (default)
        self.db = firestore.Client(project=Config.PROJECT_ID, database=Config.FIRESTORE_DB)
        self.storage_client = storage.Client(project=Config.PROJECT_ID)
        self.bucket = self.storage_client.bucket(Config.BUCKET_NAME)
        logger.info("Orchestrator Initialized. Connected to Firestore and GCS.")

    def get_pending_missions(self):
        """Fetch pending missions from Firestore."""
        # Use FieldFilter for better query syntax
        from google.cloud.firestore import FieldFilter
        return self.db.collection("mission_queue").where(filter=FieldFilter("status", "==", "PENDING")).limit(1).stream()

    def load_worker(self, module_name: str):
        """Dynamically load a worker module."""
        try:
            # Import directly as we now use full package paths in registry
            return importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Failed to import worker module {module_name}: {e}")
            return None

    def execute_mission(self, doc):
        """Execute a single mission."""
        mission_data = doc.to_dict()
        mission_id = doc.id
        mission_type = mission_data.get("type") or mission_data.get("mission_type") # Handle both naming conventions
        
        logger.info(f"Processing Mission {mission_id}: {mission_type}")

        # 1. Validate Mission Type
        if mission_type not in WORKER_REGISTRY:
            logger.error(f"Unknown mission type: {mission_type}")
            doc.reference.update({
                "status": "FAILED",
                "error": f"Unknown mission type: {mission_type}",
                "completed_at": firestore.SERVER_TIMESTAMP
            })
            return

        # 2. Resolve Worker Info
        registry_entry = WORKER_REGISTRY[mission_type]
        # Class-Based Worker: (module_name, class_name, agent_id, human_name)
        module_name, class_name, agent_id, human_name = registry_entry

        # 3. Load Worker Module
        worker_module = self.load_worker(module_name)
        
        if not worker_module:
            doc.reference.update({
                "status": "FAILED",
                "error": f"Could not load module {module_name}",
                "completed_at": firestore.SERVER_TIMESTAMP
            })
            return

        # 4. Execute Heist
        try:
            # Instantiate Class and Run
            WorkerClass = getattr(worker_module, class_name)
            worker_instance = WorkerClass()
            success = worker_instance.execute()

            # 5. Update Mission Status
            status = "COMPLETED" if success else "FAILED"
            update_data = {
                "status": status,
                "worker_module": module_name,
                "completed_at": firestore.SERVER_TIMESTAMP
            }
                
            doc.reference.update(update_data)
            logger.info(f"Mission {mission_id} {status}.")

        except Exception as e:
            logger.error(f"Mission {mission_id} CRASHED: {e}")
            doc.reference.update({
                "status": "FAILED",
                "error": str(e),
                "completed_at": firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Mission {mission_id} FAILED.")

    @staticmethod
    @firestore.transactional
    def claim_mission(transaction, doc_ref):
        """Transactional mission claiming."""
        snapshot = doc_ref.get(transaction=transaction)
        if snapshot.get("status") == "PENDING":
            transaction.update(doc_ref, {"status": "IN_PROGRESS", "started_at": firestore.SERVER_TIMESTAMP})
            return True
        return False

    def run(self, run_once=False):
        """Main Orchestrator Loop."""
        logger.info(f"Orchestrator Started (Run Once: {run_once}). Waiting for missions...")
        
        # Validate Config at startup
        Config.validate()
        
        while True:
            try:
                missions = self.get_pending_missions()
                found_mission = False
                
                for doc in missions:
                    found_mission = True
                    # Transactional Claim
                    transaction = self.db.transaction()
                    if self.claim_mission(transaction, doc.reference):
                        self.execute_mission(doc)
                    else:
                        logger.warning(f"Mission {doc.id} was already claimed by another orchestrator.")
                
                if run_once:
                    if not found_mission:
                        logger.info("No pending missions found. Exiting (Run Once).")
                    else:
                        logger.info("Batch complete. Exiting (Run Once).")
                    break
                
                if not found_mission:
                    time.sleep(5) # Poll interval

            except Exception as e:
                logger.error(f"Orchestrator Loop Error: {e}")
                if run_once: break
                time.sleep(10)

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-once", action="store_true", help="Run one batch and exit")
    args = parser.parse_args()

    orchestrator = Orchestrator()
    orchestrator.run(run_once=args.run_once)
