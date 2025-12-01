# governance.py

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
import os
import yaml

from pydantic import BaseModel, Field

# === DSIE core types =========================================================

class DSIEStage(str, Enum):
    DIAGNOSE = "DSIE-01"
    STRATEGIZE = "DSIE-02"
    IMPLEMENT = "DSIE-03"
    EXECUTE = "DSIE-04"


class DiagnosisReport(BaseModel):
    stage: DSIEStage = Field(default=DSIEStage.DIAGNOSE)
    problem_summary: str
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Logs, samples, metrics, stack traces, etc."
    )
    root_cause_hypothesis: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Engineer-estimated probability that this hypothesis is correct."
    )
    alternatives_considered: List[str] = Field(default_factory=list)


class StrategyOption(BaseModel):
    name: str
    category: str  # "inversion", "stop_loss", "asymmetric_bet"
    description: str
    expected_benefit: str
    risks: List[str] = Field(default_factory=list)
    kill_switch_conditions: List[str] = Field(
        default_factory=list,
        description="Human-readable conditions that should trigger rollback."
    )


class StrategyObject(BaseModel):
    stage: DSIEStage = Field(default=DSIEStage.STRATEGIZE)
    problem_summary: str
    options: List[StrategyOption]
    recommended_option: str
    rationale: str


class ExecutionReport(BaseModel):
    stage: DSIEStage = Field(default=DSIEStage.EXECUTE)
    mission_id: Optional[str] = None
    subsystem: str
    change_summary: str
    primary_metric: str
    metric_before: float
    metric_after: float
    observation_window_hours: float
    success: bool
    notes: str = ""


# === Agent contract stub (wire this to your YAML/JSON contracts) =============

class AgentContract(BaseModel):
    agent_id: str
    human_readable_name: str
    autonomy_level: int
    primary_metric: Optional[str] = None
    # You can extend this with the full schema from agent_contract.yaml


class AgentContext(BaseModel):
    contract: AgentContract
    current_diagnosis: Optional[DiagnosisReport] = None
    current_strategy: Optional[StrategyObject] = None
    mission_id: Optional[str] = None


class GovernanceError(RuntimeError):
    pass


# === Decorators to enforce DSIE discipline ===================================

def require_diagnosis(fn: Callable) -> Callable:
    """
    Enforce that a DiagnosisReport is present in the AgentContext
    before running operations that change state (infra, data, etc.).
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        ctx: Optional[AgentContext] = kwargs.get("ctx")
        if ctx is None:
            # Try to find ctx in args if passed positionally
            for arg in args:
                if isinstance(arg, AgentContext):
                    ctx = arg
                    break
        
        if ctx is None:
            raise GovernanceError("AgentContext 'ctx' is required.")

        if ctx.current_diagnosis is None:
            raise GovernanceError(
                "DSIE-01 DiagnosisReport required before calling this function."
            )

        return fn(*args, **kwargs)

    return wrapper


def require_strategy(fn: Callable) -> Callable:
    """
    Enforce that a StrategyObject is present before Implementation/Execution.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        ctx: Optional[AgentContext] = kwargs.get("ctx")
        if ctx is None:
            for arg in args:
                if isinstance(arg, AgentContext):
                    ctx = arg
                    break

        if ctx is None:
            raise GovernanceError("AgentContext 'ctx' is required.")

        if ctx.current_strategy is None:
            raise GovernanceError(
                "DSIE-02 StrategyObject required before calling this function."
            )

        return fn(*args, **kwargs)

    return wrapper


# === System prompt scaffolding ===============================================

BASE_ROLE_TEMPLATES: Dict[str, str] = {
    "acquisitions_officer": (
        "You are the Acquisitions Officer for an automated corporation.\n"
        "You own data acquisition workers and their tests.\n"
        "You do not change infrastructure, billing, IAM, or financial accounts.\n"
    ),
    "internal_auditor": (
        "You are the Internal Auditor.\n"
        "You monitor metrics, enforce kill switches, and recommend remediation.\n"
        "You never deploy code; you only read, analyze, and open tickets.\n"
    ),
    "actuary": (
        "You are the Actuary.\n"
        "You reconcile and normalize raw datasets into a Golden Record.\n"
        "You do not modify external scrapers or cloud infrastructure.\n"
    ),
}

BASE_DSIE_SNIPPET = """
You are required to follow the DSIE discipline:

- DSIE-01 DIAGNOSE: Before proposing changes, gather evidence, summarize
  the problem, and state a falsifiable root-cause hypothesis.
- DSIE-02 STRATEGIZE: Generate multiple strategy options, including
  inversion, stop-loss, and asymmetric bets. Recommend one with rationale.
- DSIE-03 IMPLEMENT: Make minimal, reversible changes. Prefer small diffs
  over rewrites. Keep logs and metrics.
- DSIE-04 EXECUTE: Observe metrics over a defined window, compare before
  vs after, and produce an ExecutionReport. If metrics degrade beyond
  defined thresholds, trigger the kill-switch and revert.
"""

BASE_WORKING_AGREEMENTS = """
General working agreements:

- Prefer small, incremental changes over full rewrites.
- When something partially works, freeze the working part and focus on the failing stage.
- Be explicit about assumptions; log them when acting on them.
- Respect safety, compliance, and rate-limiting constraints at all times.
"""


def get_system_prompt(role: str) -> str:
    """
    Build a system prompt for a given role.

    This function intentionally keeps the prompt short and role-specific,
    and references the DSIE process instead of inlining entire constitutions.
    """
    role_key = role.lower().strip()
    
    # Try to load from contract if available (advanced)
    # For now, use the base templates
    role_block = BASE_ROLE_TEMPLATES.get(
        role_key,
        f"You are an agent with role '{role}'. Clarify your scope before acting.\n"
    )

    prompt_parts = [
        role_block.strip(),
        BASE_DSIE_SNIPPET.strip(),
        BASE_WORKING_AGREEMENTS.strip(),
    ]

    return "\n\n".join(prompt_parts)
