# Acquisition Log: Batch 6 (FBref)

## Source Details
*   **Source 17**: FBref (Soccer)

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Worker**: `worker_fbref.py`
*   **Status**: FAILED

### Steps Taken
1.  **FBref**: Scraped `https://fbref.com/en/comps/9/Premier-League-Stats` using `pd.read_html`.
    *   **Result**: FAILED (403 Forbidden). Sports Reference has tightened anti-bot measures. Requires `requests` with headers or Selenium, not raw `pd.read_html`.

## Final Status Update
*   **FBref** joins the "Anti-Bot/Gated" list.
*   **Ideal Repository** analysis is complete. Most high-value targets are either already captured (Savant, FanGraphs, NFLVerse) or require advanced stealth/payment.

## Active Pipeline Count: 13
(No new pipelines added from this batch).
