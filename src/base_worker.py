import logging
import time
import requests
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
# from fake_useragent import UserAgent # Unused
from google.cloud import storage, firestore

from src.config import Config

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseWorker(ABC):
    """
    Abstract Base Class for all Veiled Vector workers.
    Enforces Standardized Logging and Config usage.
    """
    
    def __init__(self, offline_mode: bool = False):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = Config
        self.offline_mode = offline_mode
        
        if self.offline_mode:
            self.logger.info("Worker initialized in OFFLINE MODE. Skipping GCP client connection.")
            self.storage_client = None
            self.db = None
            self.bucket = None
            # Still initialize session for offline testing if needed, or handle in methods
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": self.config.USER_AGENT
            })
            return

        # Initialize Storage
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            )
            self.storage_client = storage.Client(project=self.config.PROJECT_ID, credentials=credentials)
            self.db = firestore.Client(project=self.config.PROJECT_ID, database=self.config.FIRESTORE_DB, credentials=credentials)
        else:
            self.storage_client = storage.Client(project=self.config.PROJECT_ID)
            self.db = firestore.Client(project=self.config.PROJECT_ID, database=self.config.FIRESTORE_DB)
            
        self.bucket = self.storage_client.bucket(self.config.BUCKET_NAME)
        
        # Initialize HTTP Session with defaults and Retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.USER_AGENT
        })
        
        # Configure Retries
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @abstractmethod
    def run(self) -> bool:
        """
        Main execution logic. Must be implemented by subclasses.
        """
        pass

    def execute(self) -> bool:
        """
        Wrapper for run().
        Returns: success: bool
        """
        self.logger.info(f"Starting execution.")
        try:
            success = self.run()
            if success:
                self.logger.info("Mission Accomplished.")
            else:
                self.logger.warning("Mission Failed or Incomplete.")
            return success
        except Exception as e:
            self.logger.error(f"Critical Worker Failure: {e}")
            return False

    def upload_json(self, data: Any, path: str):
        """
        Helper to upload JSON data to GCS.
        """
        if self.bucket is None:
            self.logger.info(f"[OFFLINE] Would upload to gs://{self.config.BUCKET_NAME}/{path}")
            return

        blob = self.bucket.blob(path)
        blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
        self.logger.info(f"Uploaded: gs://{self.config.BUCKET_NAME}/{path}")
