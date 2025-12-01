# Acquisition Log: Batch 4 (Final Sweeps)

## Source Details
*   **Source 4**: Umpire Scorecards

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Worker**: `worker_umps.py`
*   **Status**: FAILED

### Steps Taken
1.  **Umpire Scorecards**: Scraped `https://umpscorecards.com/games/`.
    *   **Result**: FAILED (404). Endpoint changed or site structure updated.

## Final Exhaustive Summary
I have attempted to harvest data from all 32 sources listed in "Free Sports Data Harvesting Analysis.md".

### Successes (Data Flowing)
1.  **Baseball Savant** (Source 1) - via `pybaseball`
2.  **FanGraphs** (Source 2) - via `pybaseball`
3.  **Baseball Reference** (Source 3) - via `pybaseball`
4.  **NFLVerse** (Source 6, 8, 12) - via `nfl_data_py`
5.  **NFLPenalties.com** (Source 7) - via Scraping
6.  **NBAStuffer** (Source 11) - via Scraping
7.  **NHL API** (Source 15) - via API
8.  **UFCStats** (Source 16) - via Scraping
9.  **FastF1** (Source 18) - via `fastf1`
10. **Tennis Abstract** (Source 19) - via GitHub CSV
11. **RotoGrinders Weather** (Source 31) - via Scraping
12. **NOAA** (Source 30 Substitute) - via API
13. **SEC EDGAR** (Bonus) - via API

### Blockers (Requires Action/Money)
*   **API Keys Needed**: CollegeFootballData (5), The Odds API (22).
*   **Subscriptions Needed**: KenPom (9), Cleaning the Glass (10), Dunks & Threes (12), Evolving Hockey (14), Don Best (26).
*   **Anti-Bot/Gated**: Pinnacle (23), Circa (24), Bookmaker (25).
*   **Broken/Changed**: Oracle's Elixir (21), Umpire Scorecards (4).

The "Sports Analytics Department" is now operational with **13 active data pipelines**.
