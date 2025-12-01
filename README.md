# Veiled Vector Core

The "Sports Analytics Department" of the Automated Corporation.
This project serves as the edge data ingestion hub, running locally to leverage residential IP addresses for scraping.

## Setup

1.  **Clone & Environment**
    ```bash
    git clone <repo-url>
    cd veiled-vector-core
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Configuration**
    - Copy `.env.example` to `.env` and fill in your GCP details.
    - Ensure you have `credentials.json` (Service Account Key) in the root if running locally (DO NOT COMMIT THIS).

3.  **Running Locally**
    ```bash
    # Run Orchestrator (Main Loop)
    python3 -m src.orchestrator
    
    # Run Orchestrator (One Batch)
    python3 -m src.orchestrator --run-once
    
    # Or with venv python directly
    ./venv/bin/python -m src.orchestrator --run-once
    ```

4.  **Dashboard**
    - The dashboard is a Next.js app in `dashboard/`.
    - `cd dashboard && npm install && npm run dev`

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Workers

All workers are located in `src/workers/` and inherit from `src/base_worker.py`.
They are orchestrated by `src/orchestrator.py` based on missions in Firestore.
