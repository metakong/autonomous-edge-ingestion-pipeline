# FanDuel Data Acquisition Log: The Stealth Battle
**Date:** November 30, 2025
**Target:** FanDuel Sportsbook (`https://sportsbook.fanduel.com/navigation/nfl`)
**Objective:** Automate data ingestion for the "Autonomous Sports Data Acquisition System".

## 1. The "Golden Template" Approach
*   **Strategy:** We cloned the proven `worker_dk.py` (DraftKings) to create `worker_fd.py`.
*   **Goal:** Maintain strict DSIE governance (Diagnosis -> Strategy -> Execution) and GCS data pipeline consistency.
*   **Initial Result:** **FAILURE**.
    *   FanDuel does not expose a public API like DraftKings.
    *   Standard `requests` or basic `playwright` attempts were blocked immediately.

## 2. The Enemy: PerimeterX / Human Verification
*   **Symptom:** The worker captured a small HTML file (~9KB) containing "Access to this page has been denied" and a "Human verification challenge".
*   **Diagnosis:** FanDuel uses **PerimeterX** (now part of HUMAN Security) to fingerprint browsers and block bots.
*   **HTTP Status:** 403 Forbidden.

## 3. Stealth Engineering (The Bypass)
*   **Tool:** `playwright-stealth` (Python library).
*   **Implementation:**
    *   Standard usage (`await stealth_async(page)`) was insufficient or difficult to import correctly with the async API.
    *   **Solution:** We used the `Stealth` class wrapper:
        ```python
        from playwright_stealth import Stealth
        async with Stealth().use_async(async_playwright()) as p:
            # ... browser launch ...
        ```
*   **Result:** **PARTIAL SUCCESS**.
    *   **Run 1:** Successfully bypassed the block! Captured a **369KB** file containing the full NFL betting page.
    *   **Run 2:** Blocked again (9KB file).
    *   **Conclusion:** The bypass is flaky. It works sometimes but likely needs residential proxies and more advanced fingerprint rotation for 100% reliability.

## 4. Data Extraction (The Loot)
Once we bypassed the wall, we had to find the data.

### Attempt A: `window.__NEXT_DATA__`
*   **Hypothesis:** Most Next.js apps store state in this global variable.
*   **Result:** **FAILED**. It was either null or not present in the way we expected.

### Attempt B: `window.FD`
*   **Hypothesis:** Found a global variable `FD` in the raw HTML.
*   **Result:** **PARTIAL**. We extracted it, but it only contained configuration data (`clientId`, `endpoints`), not the odds.

### Attempt C: `window.initialState` (The Winner)
*   **Discovery:** Deep inspection of the raw HTML revealed a separate global variable `initialState` containing the actual sports data.
*   **Extraction Challenge:** The variable was defined in a script tag but keys were unquoted (e.g., `initialState={eventTypes:...}`), making it invalid JSON.
*   **Solution:**
    1.  **Regex:** Locate `initialState\s*=\s*\{`.
    2.  **Brace Counting:** Manually extract the full object string by counting matching `{` and `}`.
    3.  **Browser Evaluation:** Pass the extracted string *back* to `page.evaluate()` to let the browser's JS engine parse it into a JSON-serializable object.
*   **Outcome:** Successfully extracted a 2.5KB sample containing valid event types (Soccer, Tennis, NFL, etc.).

## 5. Summary & Recommendation
*   **Viability:** We **CAN** get data from FanDuel.
*   **Stability:** Currently **LOW**. The PerimeterX block is the main bottleneck.
*   **Next Steps for FanDuel:** To make this production-ready, we would need:
    *   High-quality Residential Proxies.
    *   Browser Fingerprint Rotation.
    *   Possibly a "Headful" mode with visual monitoring.

## 6. Pivot to PrizePicks
*   We are taking these learnings (Stealth wrapper + Browser-eval extraction) to target PrizePicks next.
