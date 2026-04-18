import requests
import json
import time
import logging
import os
import sys
from fake_useragent import UserAgent

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class GraphQLWorker(BaseWorker):
    """
    Worker for querying SportTrade GraphQL API.
    """
    URL = "https://scorekeeper.prod.east.sporttrade.app/graphql"
    
    # The Payload (GraphQL Query)
    GRAPHQL_QUERY = """
    query EventMarketsBySlug($slug: String!) {
      eventBySlug(slug: $slug) {
        id
        name
        markets {
          id
          name
          outcomes {
            id
            name
          }
        }
      }
    }
    """
    GRAPHQL_VARIABLES = {
        "slug": "pittsburgh-steelers-buffalo-bills-2025-11-30"
    }

    def validate_graphql_data(self, data: dict) -> bool:
        """Edge Data Integrity Check for GraphQL Response."""
        if not data:
            self.logger.error("Validation Failed: Empty response")
            return False
        if "data" not in data:
            self.logger.error("Validation Failed: 'data' key missing")
            return False
        if data["data"] is None:
            self.logger.error("Validation Failed: 'data' is null")
            return False
        return True

    def run(self) -> bool:
        self.logger.info(f"Initiating GraphQL Heist for: {self.GRAPHQL_VARIABLES['slug']}")
        
        ua = UserAgent()
        
        # The Headers (Stealth Mode)
        headers = {
            "User-Agent": ua.random,
            "Content-Type": "application/json",
            "Origin": "https://platform.getsporttrade.com",
            "Referer": "https://platform.getsporttrade.com/",
            "x-device-id": "DELL-WORKER-v6" 
        }
        
        try:
            # Send the POST request
            response = self.session.post(
                self.URL,
                json={"query": self.GRAPHQL_QUERY, "variables": self.GRAPHQL_VARIABLES},
                headers=headers,
                timeout=15
            )
            
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            
            # Verify we got data, not an error
            if "errors" in data:
                 self.logger.error(f"GraphQL Error: {data['errors']}")
                 return False

            if self.validate_graphql_data(data):
                self.logger.info("Heist Successful. Data acquired.")
                
                # --- HEAVY LIFTING TO GCS ---
                filename = f"graphql_decoder_{int(time.time())}.json"
                self.upload_json(data, f"raw_data/{filename}")
                self.logger.info(f"Decoder Ring Uploaded: gs://{self.config.BUCKET_NAME}/raw_data/{filename}")
                
                # GENERATE EXECUTION REPORT
                return True
            else:
                self.logger.warning("   -> GraphQL validation failed.")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
