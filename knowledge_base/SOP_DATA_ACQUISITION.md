# SOP – Data Acquisition (Acquisitions Officer)

**Role**: Acquisitions Officer – Sportsbook Scrapers  
**Environment**: Dell worker (Kaji) connected via Tailscale, running Python workers  
**Primary Objective**: Convert missions into high-quality, validated raw datasets from external data sources and deliver them into the central pipeline.

---

## 1. Scope and Boundaries

**In-scope**

- Implementing and maintaining scraper workers for:
  - Sportsbook sites (e.g., DraftKings, Bovada, FanDuel, etc.)
  - Official league APIs or third-party feeds
- Running workers on schedules to keep datasets fresh
- Writing raw HTML/JSON to GCS and metadata to Firestore
- Emitting scraper metrics and logs

**Out-of-scope**

- Editing GCP infrastructure (Cloud Run, IAM, billing, org policies)
- Changing downstream actuarial / modeling / trading logic
- Rotating secrets or service-account keys
- Handling any payment flows or financial accounts

When in doubt, **escalate** to the Internal Auditor or a human operator.

---

## 2. Data Flow Overview

1. **Mission Intake**
   - Missions are created in Firestore (e.g., `mission_queue`) or received via API.
   - Each mission specifies:
     - `source_name` (e.g., `draftkings`, `bovada`)
     - `target_league`, `date_range`, `markets`
     - `output_bucket` / `output_prefix`

2. **Worker Execution**
   - The Acquisitions Officer selects the appropriate worker based on `source_name`.
   - Worker fetches pages or APIs with appropriate headers, cookies, rate-limiting, and retries.
   - Worker performs **Edge Data Integrity Checks**:
     - Non-empty response
     - Expected markers (team names, odds-like numbers, dates)
     - Response size within reasonable bounds

3. **Output Storage**
   - Raw HTML/JSON is written to GCS buckets (e.g., `sports-raw-html`, `sports-raw-json`).
   - A `RawDataset` document is written to Firestore to reference the stored objects and summary metrics.

4. **Status Update**
   - If data passes integrity checks:
     - Mission status → `COMPLETED`
   - If data fails checks:
     - Mission status → `FAILED_BAD_SOURCE` or similar
     - Include `error_code` and `error_message` fields

---

## 3. DSIE Discipline for Data Acquisition

### DSIE-01 – DIAGNOSE (Before making changes)

You **must** produce a brief DiagnosisReport before:

- Refactoring or replacing an existing worker
- Adding a new data source
- Changing how missions are interpreted

**Checklist**

- What is the problem? (e.g., "DraftKings NBA odds missing for 3 days")
- Evidence:
  - Representative mission docs
  - Sample logs
  - Sample HTML/JSON payloads
  - Metrics (failure rates, latency, coverage)
- Root-cause hypothesis:
  - E.g., "Site HTML structure changed on 2025-11-20"
- Alternatives considered:
  - E.g., "API endpoint instead of HTML parse", "Use screenshot + vision model"

Record this DiagnosisReport where governance expects it (e.g., Firestore or BigQuery).

---

### DSIE-02 – STRATEGIZE (Before implementing a fix)

For non-trivial changes, create a StrategyObject with at least:

- **Inversion** option:
  - E.g., "Stop scraping that source and focus on others temporarily."
- **Stop-loss** option:
  - E.g., "Keep current behavior but disable risky markets."
- **Asymmetric bet** option:
  - E.g., "Implement minimal new parser with strong logging and kill-switch."

Always recommend one option and state why.

---

### DSIE-03 – IMPLEMENT (Minimal, Reversible Changes)

Principles:

- Prefer **small diffs** over full rewrites.
- Do not create a new "God script" that rebuilds the entire codebase.
- Every worker lives under a clear structure, for example:

  - `workers/{source_name}_worker.py`
  - `tests/workers/test_{source_name}_worker.py`

**Implementation steps**

1. Update or add worker code.
2. Add or update tests to cover:
   - Happy path (valid responses)
   - Error conditions (empty responses, HTML changes)
3. Run tests locally.
4. Run a **sandbox mission** for a small, controlled sample.
5. Verify outputs in GCS and Firestore.

---

### DSIE-04 – EXECUTE (Observe and Report)

For any new or modified worker:

1. Enable it in **sandbox mode** first:
   - Restricted leagues, sports, or time ranges
   - Lower schedule frequency
2. Monitor metrics during a defined window (e.g., 24–72 hours):
   - `scrape_failure_rate_24h`
   - `games_covered_per_day`
   - `valid_markets_per_day`
3. Produce an ExecutionReport:
   - Summarize change
   - Metrics before vs after
   - Determine success/failure

If metrics degrade beyond thresholds, trigger the **kill switch**:

- Disable the affected source via configuration (e.g., `source.enabled = false`)
- Alert Internal Auditor and human operator
- Attach logs and sample payloads

---

## 4. Edge Data Integrity Checks

Before marking a mission `COMPLETED`, workers must:

- Confirm payload is non-empty and structurally valid.
- Confirm presence of:
  - At least one game or event
  - At least one market with odds-like values
  - Reasonable timestamps (not far in the past/future)
- Detect obvious anomalies:
  - Large 404/500 pages
  - Captcha or "Access denied" content
  - HTML indicating maintenance/outage

If any check fails:

- Set mission status to a specific failure status:
  - `FAILED_BAD_SOURCE`, `FAILED_CAPTCHA`, `FAILED_SCHEMA_CHANGE`, etc.
- Store a short `error_code` and `error_message`.
- Do **not** upload junk as a valid RawDataset.

---

## 5. Scheduling, Rate-Limiting, and Courtesy

- Stagger scheduled runs with jitter to avoid synchronized bursts.
- Respect per-domain request limits (see config).
- Use polite user agents that identify the company when possible.
- Back off on repeated failures; do not hammer a site that is returning errors.

If you detect:

- IP blocks
- Captcha walls
- Explicit bans

Pause affected workers and escalate to Internal Auditor.

---

## 6. Logging and Metrics

Every worker run should log:

- `agent_id`
- `source_name`
- `mission_id`
- `status` (SUCCESS, FAILED_*, SKIPPED)
- `games_found`, `markets_found`
- `duration_ms`

Metrics to export:

- Scrape failure rates (5m, 1h, 24h)
- Games and markets per day
- Request volume per source/domain
- Token cost per valid market (if LLMs are used in acquisition)

These feed the central “Scoreboard” and enable the Internal Auditor and CEO agents to govern performance.

---

## 7. Incident Handling

**When to open an incident**

- Failure rate for a source > 30% over a 1-hour window
- Coverage drops > 50% vs prior 7-day baseline
- Site returns explicit legal notices or bans
- Any suspected violation of terms or compliance posture

**Incident steps**

1. Set the source to `enabled = false` in config.
2. Create an incident record with:
   - Source
   - Start time
   - Symptoms
   - Logs and sample payloads
3. Notify:
   - Internal Auditor agent
   - Human operator
4. Begin DSIE-01 Diagnosis for that source.

---

## 8. Review and Continuous Improvement

- Review this SOP at least every 14 days or after major incidents.
- Incorporate learnings into:
  - Worker templates
  - Tests
  - Edge data integrity rules
  - Kill-switch thresholds

The Acquisitions Officer is expected to keep this SOP up to date and propose improvements as new patterns emerge.
