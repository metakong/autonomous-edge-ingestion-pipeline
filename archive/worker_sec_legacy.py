import requests
import json
import time
import os
import logging
import sys
from google.cloud import storage

# IMPORT GOVERNANCE LAYERS
sys.path.append(os.path.join(os.getcwd(), "src"))
from governance import require_diagnosis, AgentContext, AgentContract, DiagnosisReport, ExecutionReport, DSIEStage

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [KAJI-SEC] - %(levelname)s - %(message)s')
logger = logging.getLogger("KajiSEC")

# CONFIG
PROJECT_ID = "veiled-vector-core"
BUCKET_NAME = f"veiled-vector-data-{PROJECT_ID}"
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)

# SEC API
# User-Agent MUST be in format: "Company Name email@example.com"
HEADERS = {
    "User-Agent": "Veiled Vector Core deardorff.sean@gmail.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov"
}

# Target: DraftKings Inc.
CIK = "0001772757"
# SEC requires 10-digit CIK in URL
CIK_PADDED = CIK.zfill(10)

def validate_filing(content: bytes, name: str) -> bool:
    """Edge Data Integrity Check for SEC Filings."""
    if not content:
        logger.error(f"Validation Failed: {name} is empty")
        return False
    # Basic check for HTML or text content
    if len(content) < 1000:
        logger.warning(f"Validation Warning: {name} is suspiciously small ({len(content)} bytes)")
        return False
    return True

@require_diagnosis
def execute_heist(ctx: AgentContext):
    logger.info("Governance Check Passed. Infiltrating SEC EDGAR...")
    start_time = time.time()
    
    try:
        # Step 1: Get Submission History
        url = f"https://data.sec.gov/submissions/CIK{CIK_PADDED}.json"
        logger.info(f"Fetching filing history for CIK {CIK}...")
        
        resp = requests.get(url, headers=HEADERS, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"SEC Access Denied: {resp.status_code} - {resp.text}")
            return False
            
        data = resp.json()
        filings = data["filings"]["recent"]
        
        # Step 2: Find latest 10-K
        logger.info("Scanning for latest 10-K...")
        accession_number = None
        primary_doc = None
        report_date = None
        
        for i, form in enumerate(filings["form"]):
            if form == "10-K":
                accession_number = filings["accessionNumber"][i]
                primary_doc = filings["primaryDocument"][i]
                report_date = filings["reportDate"][i]
                logger.info(f"Found 10-K from {report_date}")
                break
        
        if not accession_number:
            logger.error("No 10-K found in recent filings.")
            return False
            
        # Step 3: Download the 10-K
        # URL Format: https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_dashes}/{primary_doc}
        accession_no_dashes = accession_number.replace("-", "")
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{accession_no_dashes}/{primary_doc}"
        
        logger.info(f"Downloading document from {doc_url}...")
        # Note: www.sec.gov has different host/headers requirements sometimes, but usually same UA works
        doc_headers = {"User-Agent": "Veiled Vector Core deardorff.sean@gmail.com"}
        doc_resp = requests.get(doc_url, headers=doc_headers, timeout=20)
        
        if doc_resp.status_code == 200:
            if validate_filing(doc_resp.content, "10-K Filing"):
                filename = f"sec_draftkings_10k_{report_date}.htm"
                blob = bucket.blob(f"results/{filename}")
                blob.upload_from_string(doc_resp.content, content_type='text/html')
                
                logger.info(f"LOOT SECURED: gs://{BUCKET_NAME}/results/{filename}")
                
                # GENERATE EXECUTION REPORT
                report = ExecutionReport(
                    stage=DSIEStage.EXECUTE,
                    subsystem="worker_sec",
                    change_summary="SEC 10-K Download",
                    primary_metric="bytes_secured",
                    metric_before=0.0,
                    metric_after=float(len(doc_resp.content)),
                    observation_window_hours=0.01,
                    success=True,
                    notes=f"Secured: {len(doc_resp.content)} bytes (10-K)"
                )
                
                # UPLOAD REPORT
                timestamp = int(time.time())
                report_filename = f"report_sec_{timestamp}.json"
                blob_report = bucket.blob(f"governance/executions/{report_filename}")
                blob_report.upload_from_string(report.model_dump_json(indent=2), content_type='application/json')
                logger.info(f"REPORT FILED: gs://{BUCKET_NAME}/governance/executions/{report_filename}")
                
                return True
            else:
                logger.warning("   -> Filing validation failed.")
                return False
        else:
            logger.error(f"Download failed: {doc_resp.status_code}")
            return False

    except Exception as e:
        logger.error(f"Heist Failed: {e}")
        # Generate Failure Report
        try:
            fail_report = ExecutionReport(
                stage=DSIEStage.EXECUTE,
                subsystem="worker_sec",
                change_summary="SEC Scrape (FAILED)",
                primary_metric="bytes_secured",
                metric_before=0.0,
                metric_after=0.0,
                observation_window_hours=0.01,
                success=False,
                notes=str(e)
            )
            timestamp = int(time.time())
            blob_fail = bucket.blob(f"governance/executions/fail_sec_{timestamp}.json")
            blob_fail.upload_from_string(fail_report.model_dump_json(indent=2), content_type='application/json')
        except Exception as report_error:
            logger.error(f"Could not file failure report: {report_error}")
        return False

if __name__ == "__main__":
    # DEFINE THE AGENT
    contract = AgentContract(
        agent_id="acquisitions_officer_04",
        human_readable_name="Acquisitions Officer (SEC)",
        autonomy_level=2
    )

    # TEST: RUN WITH DIAGNOSIS
    print("\n--- ATTEMPT: Running with valid paperwork ---")
    report = DiagnosisReport(
        problem_summary="Need corporate financials for competitor analysis",
        root_cause_hypothesis="Routine ingestion schedule",
        confidence=1.0
    )
    good_ctx = AgentContext(contract=contract, current_diagnosis=report)
    execute_heist(ctx=good_ctx)
