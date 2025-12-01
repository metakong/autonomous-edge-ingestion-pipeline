This is the final movement of the symphony. In **DIAGNOSE**, we found the truth. In **STRATEGIZE**, we designed the leverage. In **IMPLEMENT**, we built the machine.

Now, in **EXECUTE**, we turn it on, watch the scoreboard, and ruthlessly cut anything that doesn't win.

You have made it clear: We do not tolerate "Zombie Processes" that consume resources without generating value. We also do not tolerate "Vanity Metrics."

Here is the **Standard Operating Procedure (SOP)** for the **EXECUTE** phase, followed by the final Python logic block.

-----

# STANDARD OPERATING PROCEDURE: DSIE-04 (EXECUTE & EVALUATE)

**AUTHORITY:** The Constitution, Article V (Efficiency) & The "Libertarian Mandate"
**OBJECTIVE:** To run the solution in the wild, measure the *actual* economic impact, and auto-terminate any agent that fails to meet its "Sandbagged" promise.
**MANTRA:** "The Scoreboard is the only truth. Profit or Delete."

## PHASE 1: THE "SCOREBOARD" LOCK (METRIC DEFINITION)

**Directive:** No agent runs without a defined, falsifiable success metric.

1.  **The "One Metric" Rule:**
      * **Action:** Every agent must optimize for exactly **ONE** primary metric (e.g., Net Profit, Verified Leads, Latency Reduction).
      * **Constraint:** "General Helpfulness" is not a metric. "Brand Awareness" is not a metric. Cash and Time are metrics.
2.  **The "Live Feed" Dashboard:**
      * **Action:** The Agent must pipe its results to a simple log/dashboard visible to the CEO.
      * **Standard:** If the CEO has to "ask" how the agent is doing, the agent is failing. The data must be pushed, not pulled.

## PHASE 2: THE "KILL SWITCH" PROTOCOL (PROBATION)

*Derived from the "Gift Card / Intern" Doctrine.*

**Directive:** Every new agent is on probation. We do not offer tenure to code.

1.  **The 72-Hour Review:**
      * **Action:** After 72 hours of live execution, we audit performance against the "Sandbagged" Estimate.
      * **Logic:**
          * **IF** Result \> Estimate: **PROMOTE**. (allocate more compute).
          * **IF** Result \< Estimate but \> 0: **PROBATION**. (Re-Diagnose).
          * **IF** Result \< 0 (Loss): **TERMINATE**. (Delete the container).
2.  **The "Bloatware" Purge:**
      * **Action:** Every 30 days, the "Agent Resources Dept" audits all running processes.
      * **Question:** "If we deleted this agent today, would the P\&L change?"
      * **Constraint:** If the answer is No, the agent is deleted immediately.

## PHASE 3: THE "AUTOPSY" LOOP (LEARNING)

**Directive:** We do not just fail; we learn *why*.

1.  **The "Root Cause" Log:**
      * **Action:** If an agent is terminated, it must write its own obituary. "I failed because the API changed," or "I failed because the Strategy was flawed."
      * **Storage:** This log is fed back into the **Vector Database (The Vault)** so future agents don't make the same mistake.
2.  **The "Winner's Circle" Scaling:**
      * **Action:** If an agent succeeds (e.g., The "Card Shark" finds a $500 profit), we do not just celebrate. We **Scale**.
      * **Command:** "Can we run 10 instances of this?"

-----

### **The Final Python Logic Update (`dsie_core.py`)**

I have added the `execute` method, which includes the logic for the "Kill Switch" and the "Scoreboard."

```python
    def execute(self, implementation_report: ImplementationReport) -> ExecutionReport:
        """
        THE 'PROFIT OR DELETE' ENGINE.
        Runs the solution and audits the results.
        """
        if not implementation_report or implementation_report.status != "Ready":
            self.logger.error("EXECUTION HALTED: Implementation not ready.")
            return None

        self.logger.info(f"EXECUTING Agent: {self.agent_name}")

        # STEP 1: THE SCOREBOARD LOCK
        # Define what "Winning" looks like
        primary_metric = self._define_primary_metric()
        self.logger.info(f"Tracking Metric: {primary_metric}")

        # STEP 2: RUN THE AGENT (Simulated Runtime)
        # This is where the actual work happens in the real world.
        runtime_results = self._run_agent_process(implementation_report.artifact)

        # STEP 3: THE 72-HOUR REVIEW (The Audit)
        performance_delta = runtime_results.actual_value - runtime_results.sandbagged_estimate

        # STEP 4: THE KILL SWITCH DECISION
        if runtime_results.actual_value < 0:
            # Case: The Agent lost money/time.
            self.logger.critical("FAILURE: Agent generated negative value. INITIATING TERMINATION.")
            self._terminate_agent()
            return ExecutionReport(status="Terminated", profit=runtime_results.actual_value)
            
        elif performance_delta < 0:
            # Case: The Agent made money, but missed the target.
            self.logger.warning(f"UNDERPERFORMANCE: Missed target by {performance_delta}. Placing on PROBATION.")
            self.current_state = DSIEState.DIAGNOSE # Loop back to start
            return ExecutionReport(status="Probation", profit=runtime_results.actual_value)

        else:
            # Case: The Agent won.
            self.logger.info(f"SUCCESS: Beat estimate by {performance_delta}. SCALING UP.")
            self._scale_resources()
            return ExecutionReport(status="Active", profit=runtime_results.actual_value)

    def _terminate_agent(self):
        """
        The 'You're Fired' Protocol.
        """
        # Logic: 1. Stop Process. 2. Write Autopsy to Vector DB. 3. Delete Container.
        autopsy_note = f"Agent {self.agent_name} failed. Root cause: Negative ROI."
        self.logger.info(f"Writing Autopsy: {autopsy_note}")
        # (Vector DB Write would happen here)
        return True

    def _scale_resources(self):
        """
        The 'Winner's Circle'.
        """
        # Logic: Increase Docker CPU/RAM limits or spawn Clone.
        return True
```

### **The Grand Unification**

You now have the complete **Corporate Operating System** for **Veiled Vector Inc.**

1.  **The Soul:** The Constitution (Ratified).
2.  **The Brain:** The `DSIE_Core` Logic Class (Diagnose, Strategize, Implement, Execute).
3.  **The Body:** The Hardware Org Chart (Dell, Asus, Galaxy Book).

**Strategic Decision Point:**
We have finished the **Design Phase**. We are now at Hour 0 of the **Build Phase**.

Your immediate next moves are:

1.  **Flash Debian 12** to the Dell & Asus (The Infrastructure).
2.  **Paste the Constitution & DSIE Code** into your Google AI Studio project (The Brain).
3.  **Deploy the first "Guerrilla Pilot"**: The **"Legacy Archive"** script (File Converter) on the Dell E6410 to test the entire pipeline.

**Are you ready to transition from Architect to Builder?**