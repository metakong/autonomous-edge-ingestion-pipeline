# 🏈 Autonomous Edge-Ingestion Pipeline

## The Vision: The Data Engine for Vertex AI Sports Analytics 📈
Welcome to the **Autonomous Edge-Ingestion Pipeline**. This is the specialized "Scout" for high-performance sports analytics. It's engineered to harvest raw intelligence from the edge and funnel it into a **Google Cloud Data Lake**, specifically designed to feed **Vertex AI** for complex predictive modeling, custom Expected Value (EV) calculators, and advanced sports engines.

Whether you're looking for the edge in Orchard Park or tracking telemetry in Bahrain, this system provides the raw fuel for your predictive "Brain." 🧠

---

## 🕵️‍♂️ The Scouting Report: Current Capabilities
This is a robust, modular foundation built with **Advanced Python (OOP)**. While it's a powerful starter kit, please note that the sports data landscape is dynamic. In recent tests, approximately **50% of the ingestion scripts** were successful—this is a "living" project that thrives on community maintenance and forks.

### 📋 Current Intel (The "Loot"):
*   **🏈 NFL (via nflverse)**: Specialized ingestion of **2024 Season Play-by-Play** data in CSV format.
*   **🏒 NHL**: Comprehensive extraction of the **Current Game Schedule** and deep-dive GameCenter **Boxscores**.
*   **🏎️ F1 (via fastf1)**: High-fidelity telemetry (4Hz), lap times, and session data for the **2024 Bahrain Grand Prix**.
*   **⚡ Betting Markets**: Real-time odds extraction from **DraftKings** (Nash API) and **FanDuel** (Playwright Stealth extraction of `initialState`).
*   **☁️ Contextual Data**: Integration with **NOAA** and **RotoGrinders** for hyper-local stadium weather and game-day environmentals.

---

## 🛠️ Developer Onboarding: Get in the Game
This project is built for the "Builders." I don't have the time to maintain it solo anymore, but I’d love to see you fork it and make it your own beloved tool. 🦬💨

### 1. Local Environment Setup
1.  **Fork & Clone**: Get the code to your edge device (residential IPs recommended for anti-bot resilience).
2.  **Environment**: Copy `.env.example` to `.env`. Fill in your `PROJECT_ID`, `BUCKET_NAME`, and `FIRESTORE_DB`.
3.  **Credentials**: Place your GCP Service Account `credentials.json` in the root (ensure it's in `.gitignore`!).

### 2. Cloud Infrastructure (The Brain)
1.  **GCS**: Create a bucket to act as your **Data Lake**.
2.  **Firestore**: Initialize a database (Native Mode) to serve as your **Mission Queue**.

### 3. Execution
1.  **Spin up the venv**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Run the Orchestrator**:
    ```bash
    # Start the harvesting loop
    python3 -m src.orchestrator
    ```
3.  **Edge Deployment**: Use `run.sh` for rapid, backgrounded execution on your local hardware.

Let's build something legendary. Go Bills! 🏈🏒🏎️
