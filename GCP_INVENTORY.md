# GCP Inventory Report
**Project**: `veiled-vector-core`
**Date**: 2025-11-30

## 1. Compute (Cloud Run)
| Service Name | URL | Latest Revision |
| :--- | :--- | :--- |
| `veiled-vector-orchestrator` | [Link](https://veiled-vector-orchestrator-kzld2m5qwa-uc.a.run.app) | `...00026-27c` |

*No active Cloud Run Jobs found.*

## 2. Storage (GCS)
| Bucket Name | Location | Class | Purpose |
| :--- | :--- | :--- | :--- |
| `veiled-vector-data-veiled-vector-core` | US-CENTRAL1 | STANDARD | Primary Data Lake |
| `veiled-vector-core_cloudbuild` | US | STANDARD | Build Artifacts |

## 3. Scheduling & Messaging
*   **Cloud Scheduler**: No jobs found.
*   **Pub/Sub**: No topics found.

## 4. Database (Firestore)
*   **Status**: Active
*   **Database**: `veiled-vector-core-firestore` (Native Mode, us-central1)
*   **Collections**: `mission_queue`, `RawDataset`

## 5. Security & Identity
### Secrets (Secret Manager)
| Secret Name | Created |
| :--- | :--- |
| `DRIVE_SERVICE_ACCOUNT_KEY` | 2025-11-29 |
| `GOOGLE_AI_STUDIO_KEY` | 2025-11-30 |
| `TAILSCALE_AUTH_KEY` | 2025-11-30 |

### Service Accounts (IAM)
| Email | Display Name |
| :--- | :--- |
| `vector-archivist@...` | vector-archivist |
| `813376341042-compute@...` | Default compute service account |

## 6. Enabled Capabilities (Top APIs)
- **AI**: Vertex AI, Google AI Studio (implied by key)
- **Data**: BigQuery, Dataplex, Analytics Hub
- **Infra**: Cloud Run, Cloud Build, Cloud Scheduler
- **Storage**: Cloud Storage (`veiled-vector-data-veiled-vector-core`), Drive API (Legacy/Ingest)
