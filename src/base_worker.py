import logging
import time
import requests
import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
# from fake_useragent import UserAgent # Unused
from google.cloud import storage, firestore

from src.governance import require_diagnosis, AgentContext, ExecutionReport, DSIEStage
from src.config import Config

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BaseWorker(ABC):
    """
    Abstract Base Class for all Veiled Vector workers.
    Enforces Governance, Standardized Logging, and Config usage.
    """
    
    def __init__(self, context: AgentContext, offline_mode: bool = False):
        self.context = context
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = Config
        self.last_report_path = None
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

    @require_diagnosis
    def execute(self, ctx: AgentContext):
        """
        Wrapper for run() that enforces DSIE Governance.
        Returns: (success: bool, report_path: Optional[str])
        """
        # Ensure self.context matches the passed ctx if needed, or just use ctx.
        # The decorator has already validated ctx.
        self.logger.info(f"Starting execution for agent: {ctx.contract.human_readable_name}")
        try:
            success = self.run()
            if success:
                self.logger.info("Mission Accomplished.")
            else:
                self.logger.warning("Mission Failed or Incomplete.")
            return success, self.last_report_path
        except Exception as e:
            self.logger.error(f"Critical Worker Failure: {e}")
            return False, self.last_report_path

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

    def file_report(self, report: ExecutionReport):
        """
        Files an ExecutionReport to GCS and Firestore.
        """
        timestamp = int(time.time())
        
        # Ensure mission_id is set from context if missing in report
        if not report.mission_id and self.context.mission_id:
            report.mission_id = self.context.mission_id

        # 1. Upload to GCS
        filename = f"report_{report.subsystem}_{timestamp}.json"
        path = f"governance/executions/{filename}"
        
        if self.bucket:
            try:
                blob = self.bucket.blob(path)
                blob.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                self.last_report_path = f"gs://{self.config.BUCKET_NAME}/{path}"
                self.logger.info(f"Uploaded report to GCS: {self.last_report_path}")
            except Exception as e:
                self.logger.error(f"Failed to upload report to GCS: {e}")
        else:
            self.logger.info(f"[OFFLINE] Would upload report to {path}")

        # 2. Log to Firestore
        if self.db:
            try:
                report_data = report.model_dump()
                report_data['timestamp'] = firestore.SERVER_TIMESTAMP
                self.db.collection("execution_reports").add(report_data)
                self.logger.info(f"Report Filed to Firestore.")
            except Exception as e:
                self.logger.error(f"Failed to log report to Firestore: {e}")
        else:
            self.logger.info(f"[OFFLINE] Would log report to Firestore")
