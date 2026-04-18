import requests
import json
import time
import os
import logging
import sys

# IMPORT GOVERNANCE LAYERS
from src.base_worker import BaseWorker

class SECWorker(BaseWorker):
    """
    Worker for scraping SEC EDGAR data.
    """
    # SEC API
    # User-Agent MUST be in format: "Company Name email@example.com"
    SEC_HEADERS = {
        "User-Agent": "Veiled Vector Core deardorff.sean@gmail.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov"
    }

    # Target: DraftKings Inc.
    CIK = "0001772757"
    # SEC requires 10-digit CIK in URL
    CIK_PADDED = CIK.zfill(10)

    def validate_filing(self, content: bytes, name: str) -> bool:
        """Edge Data Integrity Check for SEC Filings."""
        if not content:
            self.logger.error(f"Validation Failed: {name} is empty")
            return False
        # Basic check for HTML or text content
        if len(content) < 1000:
            self.logger.warning(f"Validation Warning: {name} is suspiciously small ({len(content)} bytes)")
            return False
        return True

    def run(self) -> bool:
        self.logger.info("Infiltrating SEC EDGAR...")
        
        try:
            # Step 1: Get Submission History
            url = f"https://data.sec.gov/submissions/CIK{self.CIK_PADDED}.json"
            self.logger.info(f"Fetching filing history for CIK {self.CIK}...")
            
            # Use self.session but override headers for SEC specific requirements
            headers = self.session.headers.copy()
            headers.update(self.SEC_HEADERS)
            
            resp = self.session.get(url, headers=headers, timeout=self.config.DEFAULT_TIMEOUT)
            
            if resp.status_code != 200:
                self.logger.error(f"SEC Access Denied: {resp.status_code} - {resp.text}")
                return False
                
            data = resp.json()
            filings = data["filings"]["recent"]
            
            # Step 2: Find latest 10-K
            self.logger.info("Scanning for latest 10-K...")
            accession_number = None
            primary_doc = None
            report_date = None
            
            for i, form in enumerate(filings["form"]):
                if form == "10-K":
                    accession_number = filings["accessionNumber"][i]
                    primary_doc = filings["primaryDocument"][i]
                    report_date = filings["reportDate"][i]
                    self.logger.info(f"Found 10-K from {report_date}")
                    break
            
            if not accession_number:
                self.logger.error("No 10-K found in recent filings.")
                return False
                
            # Step 3: Download the 10-K
            # URL Format: https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number_no_dashes}/{primary_doc}
            accession_no_dashes = accession_number.replace("-", "")
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(self.CIK)}/{accession_no_dashes}/{primary_doc}"
            
            self.logger.info(f"Downloading document from {doc_url}...")
            # Note: www.sec.gov has different host/headers requirements sometimes, but usually same UA works
            doc_headers = {"User-Agent": "Veiled Vector Core deardorff.sean@gmail.com"}
            doc_resp = self.session.get(doc_url, headers=doc_headers, timeout=20)
            
            if doc_resp.status_code == 200:
                if self.validate_filing(doc_resp.content, "10-K Filing"):
                    filename = f"sec_draftkings_10k_{report_date}.htm"
                    # Use bucket directly for HTML
                    blob = self.bucket.blob(f"results/{filename}")
                    blob.upload_from_string(doc_resp.content, content_type='text/html')
                    
                    self.logger.info(f"LOOT SECURED: gs://{self.config.BUCKET_NAME}/results/{filename}")
                    
                    # GENERATE EXECUTION REPORT
                    return True
                else:
                    self.logger.warning("   -> Filing validation failed.")
                    return False
            else:
                self.logger.error(f"Download failed: {doc_resp.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Heist Failed: {e}")
            # Generate Failure Report
            return False
