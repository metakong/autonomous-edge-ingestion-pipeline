# Acquisition Log: Batch 2 (Scrapers)

## Source Details
*   **Source 7**: NFLPenalties.com (Referees)
*   **Source 11**: NBAStuffer (Rest Days)
*   **Source 16**: UFCStats.com (Fight History)
*   **Source 21**: Oracle's Elixir (Esports)

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Workers**: `worker_nflpenalties.py`, `worker_nbastuffer.py`, `worker_ufc.py`, `worker_esports.py`
*   **Status**: PARTIAL SUCCESS

### Steps Taken
1.  **NFLPenalties**: Scraped `all-positions.php`.
    *   **Result**: SUCCESS. 2024 Penalty data secured.
2.  **NBAStuffer**: Scraped `rest-days-stats`.
    *   **Result**: SUCCESS. Rest matrix secured.
3.  **UFCStats**: Scraped `completed` events.
    *   **Result**: SUCCESS. Event list secured.
4.  **Oracle's Elixir**: Attempted direct CSV download.
    *   **Result**: FAILED (404). URL needs manual update or scraping of the download page.

---

# Acquisition Log: Batch 3 (Complex/Gated)

## Source Details
*   **Source 14**: Evolving Hockey (ChickenStats)
*   **Source 31**: RotoGrinders (Weather)

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Workers**: `worker_chickenstats.py`, `worker_rotogrinders.py`
*   **Status**: MIXED

### Steps Taken
1.  **ChickenStats**: Initialized library.
    *   **Result**: BLOCKED. Library requires local CSVs from paid subscription. Worker is ready for processing once files are manually dropped.
2.  **RotoGrinders**: Scraped weather page.
    *   **Result**: SUCCESS. Raw HTML secured.

## Summary of 32 Sources Status
*   **Implemented & Verified**:
    *   Baseball (1, 2, 3)
    *   NFLVerse (6, 8, 12 - via nfl_data_py)
    *   NFLPenalties (7)
    *   NBAStuffer (11)
    *   UFCStats (16)
    *   FastF1 (18)
    *   Tennis Abstract (19)
    *   NHL API (15)
    *   RotoGrinders (31)
    *   Meteomatics (30 - Substituted with NOAA/Source 40)
*   **Blocked / Requires Credentials**:
    *   CollegeFootballData (5 - Needs Key)
    *   KenPom (9 - Needs Sub)
    *   Cleaning the Glass (10 - Needs Sub/Selenium)
    *   Dunks & Threes (12 - Needs Sub)
    *   Evolving Hockey (14 - Needs Sub)
    *   The Odds API (22 - Needs Key)
    *   Pinnacle/Circa/Bookmaker (23, 24, 25 - Anti-Bot/Gated)
    *   Don Best (26 - Paid)
*   **Failed / Needs Fix**:
    *   Oracle's Elixir (21 - 404)
