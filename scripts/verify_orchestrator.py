"""
Verify that every entry in WORKER_REGISTRY can be imported and exposes the
expected `execute_heist`-compatible interface.

Usage:
    python scripts/verify_orchestrator.py
"""

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

    # WORKER_REGISTRY values are 4-tuples: (module_name, class_name, agent_id, human_name)
    for mission_type, (module_name, class_name, agent_id, human_name) in WORKER_REGISTRY.items():
        print(f"Checking {mission_type} -> {module_name}.{class_name}...")
        try:
            module = importlib.import_module(module_name)

            # Confirm the declared class exists in the module
            if not hasattr(module, class_name):
                msg = f"{module_name} missing class '{class_name}'"
                print(f"  [FAIL] {msg}")
                failures.append(msg)
                continue

            worker_class = getattr(module, class_name)

            # Confirm the class exposes an 'execute' method (from BaseWorker)
            if not hasattr(worker_class, "execute"):
                msg = f"{class_name} missing 'execute' method (not a BaseWorker subclass?)"
                print(f"  [FAIL] {msg}")
                failures.append(msg)
                continue

            # Check the 'run' method signature includes no required positional args beyond self
            if hasattr(worker_class, "run"):
                sig = inspect.signature(worker_class.run)
                params = [
                    p for p in sig.parameters.values()
                    if p.name != "self"
                    and p.default is inspect.Parameter.empty
                ]
                if params:
                    print(
                        f"  [WARN] {class_name}.run() has unexpected required params: {params}"
                    )

            print(f"  [OK] {module_name}.{class_name} loaded.")
            successes += 1

        except Exception as e:
            msg = f"{module_name}: {e}"
            print(f"  [FAIL] Could not import: {e}")
            failures.append(msg)

    print("\n--- Summary ---")
    print(f"Successes : {successes}")
    print(f"Failures  : {len(failures)}")

    if failures:
        print("\nFailed Modules:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\nAll workers verified successfully.")
        sys.exit(0)


if __name__ == "__main__":
    verify_workers()
