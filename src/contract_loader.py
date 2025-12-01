import yaml
import os
from typing import Optional
from governance import AgentContract

CONTRACTS_DIR = os.path.join(os.getcwd(), "contracts")

def load_contract(agent_id: str) -> AgentContract:
    """
    Load an AgentContract from a YAML file in the contracts/ directory.
    
    Args:
        agent_id: The ID of the agent (e.g., 'acquisitions_officer_sports_odds').
                  This should match the filename (without .yaml) or the agent_id inside.
    
    Returns:
        AgentContract: The populated contract object.
        
    Raises:
        FileNotFoundError: If the contract file doesn't exist.
        ValueError: If the YAML is invalid or missing required fields.
    """
    # Try to find the file
    filename = f"{agent_id}.yaml"
    filepath = os.path.join(CONTRACTS_DIR, filename)
    
    if not os.path.exists(filepath):
        # Try searching for a file that contains this agent_id
        found = False
        for f in os.listdir(CONTRACTS_DIR):
            if f.endswith(".yaml"):
                full_path = os.path.join(CONTRACTS_DIR, f)
                with open(full_path, "r") as stream:
                    try:
                        data = yaml.safe_load(stream)
                        if data.get("agent_id") == agent_id:
                            filepath = full_path
                            found = True
                            break
                    except yaml.YAMLError:
                        continue
        
        if not found:
            raise FileNotFoundError(f"Contract for agent_id '{agent_id}' not found in {CONTRACTS_DIR}")

    with open(filepath, "r") as f:
        data = yaml.safe_load(f)
        
    # Map YAML fields to Pydantic model
    # Note: Our Pydantic model in governance.py is currently a stub.
    # We map what we have.
    
    return AgentContract(
        agent_id=data.get("agent_id"),
        human_readable_name=data.get("human_readable_name"),
        autonomy_level=data.get("authority", {}).get("autonomy_level", 0),
        primary_metric=data.get("success_metrics", {}).get("primary_metric")
    )
