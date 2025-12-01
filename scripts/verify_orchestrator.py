import sys
import os
import importlib
import inspect

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.orchestrator import WORKER_REGISTRY

def verify_workers():
    print("--- Verifying Worker Registry ---")
    failures = []
    successes = 0

    for mission_type, (module_name, agent_id, human_name) in WORKER_REGISTRY.items():
        print(f"Checking {mission_type} -> {module_name}...")
        try:
            module = importlib.import_module(module_name)
            if not hasattr(module, "execute_heist"):
                print(f"  [FAIL] {module_name} missing 'execute_heist'")
                failures.append(f"{module_name}: missing execute_heist")
            else:
                # Check if it's decorated (has __wrapped__ or similar, though hard to check specifically for @require_diagnosis without inspecting source)
                # We can check if it takes 'ctx' argument
                sig = inspect.signature(module.execute_heist)
                if "ctx" not in sig.parameters:
                     print(f"  [WARN] {module_name}.execute_heist signature missing 'ctx'")
                
                print(f"  [OK] {module_name} loaded.")
                successes += 1
        except Exception as e:
            print(f"  [FAIL] Could not import {module_name}: {e}")
            failures.append(f"{module_name}: {e}")

    print("\n--- Summary ---")
    print(f"Success: {successes}")
    print(f"Failures: {len(failures)}")
    
    if failures:
        print("\nFailed Modules:")
        for f in failures:
            print(f"- {f}")
        sys.exit(1)
    else:
        print("\nAll workers verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    verify_workers()
