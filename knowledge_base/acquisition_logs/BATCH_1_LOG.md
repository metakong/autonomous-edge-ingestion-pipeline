# Acquisition Log: Baseball (Sources 1, 2, 3)

## Source Details
*   **Source 1**: Baseball Savant (Statcast)
*   **Source 2**: FanGraphs (Batting Leaders)
*   **Source 3**: Baseball Reference (Standings)
*   **Method**: `pybaseball` Python library.

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Worker**: `worker_baseball.py`
*   **Status**: SUCCESS

### Steps Taken
1.  **Installation**: Installed `pybaseball` via pip.
2.  **Savant**: Called `pybaseball.statcast(start_dt, end_dt)` for yesterday's date.
    *   **Result**: Successfully retrieved pitch-level data (CSV).
3.  **FanGraphs**: Called `pybaseball.batting_stats(2024)` to get season aggregates.
    *   **Result**: Successfully retrieved batting leaderboards (CSV).
4.  **Baseball Reference**: Called `pybaseball.standings(2024)` to get divisional standings.
    *   **Result**: Successfully retrieved and concatenated standings (CSV).
5.  **Storage**: All files uploaded to `gs://veiled-vector-data-veiled-vector-core/results/baseball/`.

## Findings
*   `pybaseball` is a robust wrapper.
*   Savant data is massive; daily ingestion is preferred over bulk historical backfill for speed.
*   FanGraphs data is clean and ready for analysis.

---

# Acquisition Log: Formula 1 (Source 18)

## Source Details
*   **Source**: FastF1 (Official F1 Live Timing API Wrapper)
*   **Method**: `fastf1` Python library.

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Worker**: `worker_f1.py`
*   **Status**: SUCCESS

### Steps Taken
1.  **Installation**: Installed `fastf1` via pip.
2.  **Caching**: Enabled local file caching to prevent re-downloading large telemetry files.
3.  **Session Load**: Loaded 2024 Bahrain Grand Prix (Race).
4.  **Laps**: Extracted lap times for all drivers.
5.  **Telemetry**: Extracted high-frequency telemetry (speed, throttle, brake) for the fastest lap of the race.
6.  **Storage**: Uploaded Laps and Telemetry CSVs to `gs://veiled-vector-data-veiled-vector-core/results/f1/`.

## Findings
*   `fastf1` is extremely powerful but requires caching for performance.
*   Telemetry data is granular (4Hz+) and perfect for corner analysis.

---

# Acquisition Log: Tennis (Source 19)

## Source Details
*   **Source**: Tennis Abstract (Jeff Sackmann)
*   **Method**: Direct CSV Download from GitHub.

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Worker**: `worker_tennis.py`
*   **Status**: SUCCESS

### Steps Taken
1.  **Target**: `https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master/atp_matches_2024.csv`
2.  **Ingestion**: Used `pandas.read_csv()` to pull data directly into memory.
3.  **Storage**: Uploaded to `gs://veiled-vector-data-veiled-vector-core/results/tennis/`.

## Findings
*   Zero-friction ingestion.
*   Data is comprehensive (scores, stats, player info).

---

# Acquisition Log: NHL (Source 15)

## Source Details
*   **Source**: NHL API (Unofficial Public Endpoints)
*   **Method**: `requests` to `api-web.nhle.com`.

## Execution Log
*   **Timestamp**: 2025-11-30
*   **Worker**: `worker_nhl.py`
*   **Status**: SUCCESS

### Steps Taken
1.  **Schedule**: Hit `/v1/schedule/now` to get the current game week.
2.  **Boxscore**: Extracted the first Game ID from the schedule and hit `/v1/gamecenter/{id}/boxscore`.
3.  **Storage**: Saved JSON responses to `gs://veiled-vector-data-veiled-vector-core/results/nhl/`.

## Findings
*   The new NHL API (v1) is stable and provides rich JSON data including live play-by-play (though we only fetched boxscore for this test).
*   No authentication required.
