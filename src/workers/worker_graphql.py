import requests
import json
import time
import logging
import os
import sys
from fake_useragent import UserAgent

# IMPORT GOVERNANCE LAYERS
from src.governance import AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage
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
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem=self.__class__.__name__,
                    change_summary="GraphQL Event Data Query",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=float(len(str(data))),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(str(data))} bytes of JSON"
                )
                self.file_report(report)
                return True
            else:
                self.logger.warning("   -> GraphQL validation failed.")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem=self.__class__.__name__,
                change_summary="GraphQL Query (FAILED)",
                primary_metric="bytes_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            self.file_report(fail_report)
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_graphql",
        human_readable_name="Acquisitions Officer (GraphQL)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need specific event metadata",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    worker = GraphQLWorker(good_ctx)
    worker.execute(ctx=good_ctx)
