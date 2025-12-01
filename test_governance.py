import sys
import os

# Ensure we can import from src
sys.path.append(os.path.join(os.getcwd(), "src"))

from governance import (
    require_diagnosis, 
    AgentContext, 
    AgentContract, 
    DiagnosisReport, 
    GovernanceError
)

# --- MOCK AGENT ---
# We define a dummy agent with level 2 autonomy
mock_contract = AgentContract(
    agent_id="test_agent_01",
    human_readable_name="Test Bot",
    autonomy_level=2
)

# --- THE RESTRICTED FUNCTION ---
# This function represents a dangerous action (like deploying code)
# The decorator @require_diagnosis acts as the Guard Gate.
@require_diagnosis
def deploy_risky_code(ctx: AgentContext):
    print(">>> SUCCESS: Risky code deployed! (Governance passed)")
    return True

def run_tests():
    print("--- TEST 1: Attempting action WITHOUT Diagnosis ---")
    # Create context with NO diagnosis report
    bad_context = AgentContext(contract=mock_contract, current_diagnosis=None)
    
    try:
        deploy_risky_code(ctx=bad_context)
        print(">>> FAIL: Governance layer failed to block the action.")
    except GovernanceError as e:
        print(f">>> PASS: Governance blocked action. Error: '{e}'")

    print("\n--- TEST 2: Attempting action WITH Diagnosis ---")
    # Create context WITH a valid diagnosis report
    valid_report = DiagnosisReport(
        problem_summary="Test Problem",
        root_cause_hypothesis="Test Hypothesis",
        confidence=0.9
    )
    good_context = AgentContext(contract=mock_contract, current_diagnosis=valid_report)
    
    try:
        deploy_risky_code(ctx=good_context)
        print(">>> PASS: Governance allowed valid action.")
    except Exception as e:
        print(f">>> FAIL: Unexpected error: {e}")

if __name__ == "__main__":
    run_tests()
