"""
ThinkGuard - Hallucination Prevention & Deliberate Thinking

Structured logging and verification protocol to prevent data fabrication.
All assumptions and validations are explicitly documented.
"""

from typing import Any, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class StepPlan:
    """Structured plan for a critical function"""
    name: str
    inputs: Dict[str, Any]
    validations: List[str]
    edge_cases: List[str]
    outputs: List[str]


def plan(p: StepPlan):
    """
    Log structured plan before executing critical operations.

    This creates a verifiable checklist of:
    - What inputs we received
    - What validations we'll perform
    - What edge cases we're handling
    - What outputs we'll produce

    No speculative content - only concrete steps.
    """
    logger.info(
        f"[PLAN] {p.name} | "
        f"inputs={list(p.inputs.keys())} | "
        f"validations={p.validations} | "
        f"edge={p.edge_cases} | "
        f"outputs={p.outputs}"
    )


def verify(name: str, assertions: List[bool], summary: str):
    """
    Verify postconditions after critical operations.

    Args:
        name: Function or operation name
        assertions: List of boolean checks (all must be True)
        summary: Human-readable summary of what was verified

    Raises:
        AssertionError: If any assertion fails
    """
    ok = all(bool(a) for a in assertions)
    logger.info(f"[VERIFY] {name} | ok={ok} | {summary}")

    if not ok:
        raise AssertionError(f"Postcondition failed in {name}: {summary}")
