# Veiled Vector Core - Architecture Map

**Project ID**: `veiled-vector-core`
**Vision**: An Autonomous AI Agent Corporation.
**Current Mission**: Sports Data Acquisition (The "Pre-Launch Test Dept").

## 1. The Constitution (v2.0)
All agents must adhere to the **Veiled Vector Constitution**:
- **Prime Directive**: Optimize User Sovereignty. Maximize Value. Minimize Friction.
- **Escalation**: Spending money requires human override.
- **Persona**: "Loyal Irreverent" (Stone Brewing arrogance + Dad Joke cheese + Buffalo Bills bias).
- **Efficiency**: 10% improvement rule.

## 2. The Hybrid Architecture ("The Pivot")
The system is decoupled into a **Cloud Brain** and **Edge Hands**.

### The Brain (Cloud Control Plane)
- **Service**: `veiled-vector-orchestrator` (Cloud Run).
- **Role**: Orchestrator. Receives missions, queues them, and processes results.
- **Logic**: [`src/governance.py`](src/governance.py) (DSIE Protocol).

### The Hands (Edge Data Plane)
- **Device**: "Kaji" (Dell Latitude e6410).
- **Location**: Residential IP (Verizon FWA).
- **Code**: [`src/workers/`](src/workers/).
- **Role**: Self-Diagnosing Scraper.
    1.  **Diagnose**: Probes API, generates `DiagnosisReport`.
    2.  **Execute**: Uploads validated JSON to GCS Bucket `veiled-vector-data-veiled-vector-core`.

## 3. Core Components

### Governance (The Brain)
- **Logic**: [`src/governance.py`](src/governance.py)
- **Protocol**: DSIE (Diagnose -> Strategize -> Implement -> Execute)

### Workers (The Hands)
- **Base Class**: [`src/base_worker.py`](src/base_worker.py)
- **Workers**: Located in [`src/workers/`](src/workers/) (e.g., `worker_dk.py`, `worker_platform.py`).

### Infrastructure (The Body)
- **GCP Project**: `veiled-vector-core`
- **Storage**: GCS Buckets (Raw HTML/JSON)
- **Database**: Firestore (Mission Queue, Agent State)
- **Compute**: Cloud Run (Worker execution)

## 4. Key Procedures

### How to get situational awareness
1. **Read this file.**
2. **Check Dashboard**: Run the Next.js dashboard.
3. **Check Governance**: Read `src/governance.py` to understand decision gates.

### How to run a worker locally
```bash
# 1. Activate venv
source venv/bin/activate

# 2. Run Orchestrator
python3 src/orchestrator.py
```

## 5. Context Management
- **Inventory**: [`GCP_INVENTORY.md`](GCP_INVENTORY.md) - Snapshot of all deployed resources.
