import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """
    Centralized configuration for the Veiled Vector Core application.
    Loads values from environment variables with safe defaults where appropriate.
    """
    
    # Google Cloud Config
    PROJECT_ID = os.getenv("PROJECT_ID", "veiled-vector-core")
    BUCKET_NAME = os.getenv("BUCKET_NAME", f"veiled-vector-data-{PROJECT_ID}")
    FIRESTORE_DB = os.getenv("FIRESTORE_DB", "veiled-vector-core-firestore")
    LOCATION = os.getenv("LOCATION", "us-central1")
    
    # Worker Config
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", 30))
    USER_AGENT = os.getenv("USER_AGENT", "VeiledVector/1.0 (Internal; +https://veiled-vector.com)")

    @classmethod
    def validate(cls):
        """Ensures critical configuration is present."""
        missing = []
        if not cls.PROJECT_ID:
            missing.append("PROJECT_ID")
        
        if missing:
            raise ValueError(f"Missing critical configuration: {', '.join(missing)}")

# Configure Logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
