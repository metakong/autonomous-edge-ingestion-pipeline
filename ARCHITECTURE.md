# 🏗️ System Architecture: Edge-Cloud Distributed Ingestion

## Architectural Philosophy: "The Split" 🧠🥊
This system implements a **Decoupled Architecture** designed to maximize resilience against anti-bot measures (PerimeterX, Akamai) while maintaining a centralized control plane.

*   **The Brain (Cloud Control Plane)**: Managed via **Google Cloud Platform**. It handles state (Firestore) and persistence (GCS), allowing for downstream analytics in **Vertex AI**.
*   **The Hands (Edge Data Plane)**: Lightweight, modular workers running on local hardware. By using **Residential IPs**, we bypass the heavy-handed blocks often applied to cloud-provider IP ranges.

---

## 🛰️ Technical Blueprint: The Mission Lifecycle
The system operates on an asynchronous "Mission" model:

1.  **Queueing**: A mission (e.g., `scrape_nflverse`) is added to the **Firestore `mission_queue`**.
2.  **Polling**: The edge **Orchestrator** polls Firestore for `PENDING` missions using transactional claims to prevent race conditions.
3.  **Dynamic Loading**: The Orchestrator uses `importlib` to dynamically load the required **Worker Class**, ensuring low memory overhead.
4.  **Ingestion**: The worker executes its logic (ranging from REST API calls to **Playwright Stealth** browser automation).
5.  **Data Lake Landing**: Validated JSON or CSV payloads are uploaded directly to **Google Cloud Storage (GCS)**.
6.  **Finalization**: The mission is marked `COMPLETED` or `FAILED` with detailed logs in Firestore.

---

## 🛡️ Resilience & Engineering Maturity
*   **OOP & Abstraction**: All workers inherit from `BaseWorker`, enforcing standardized logging, configuration, and execution patterns. This uses **Abstract Base Classes (ABC)** to ensure structural integrity.
*   **Robust Session Management**: Our networking stack uses a custom `requests.Session` with built-in **Retry Logic** and **Exponential Backoff** (handling 500, 502, 503, 504 errors).
*   **Containerization**: A **Dockerfile** is included for rapid testing and deployment in containerized environments.
*   **Stability**: The system uses **Context Engineering** principles to provide agents with the necessary situational awareness to self-diagnose and report failures.

---

## ⚠️ Honesty Protocol: The Dynamic Web
**The Reality of Ingestion**: This system is a high-fidelity starter kit. Because third-party sites evolve, some workers (currently ~50% success rate) will require adjustment to match updated DOM structures or API signatures. We prioritize **Modular Code** so you can fix one worker without impacting the rest of the pipeline.

**Intended Use**: This is not a "magic button." It is a professional-grade **Data Engineering pipeline** meant to be the first step in a larger **Vertex AI** sports analytics ecosystem.
