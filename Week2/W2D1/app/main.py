"""Study-only entry points that show how Day 1 pieces connect."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

from pydantic import BaseModel

# Allow `uv run main.py` from this folder, or `python -m app.main` from W2D1.
_W2D1_ROOT = Path(__file__).resolve().parents[1]
if str(_W2D1_ROOT) not in sys.path:
    sys.path.insert(0, str(_W2D1_ROOT))

from app import config
from app.agents import langgraph_triage, sdk_assistant
from app.artifacts.handoff import build_handoff
from app.grounding.validate import validate_decision
from app.memory.checkpoints import append_tool, new_thread
from app.models import TriageDecision
from app.permissions.gates import can_run_write
from app.tools import insurance, logistics


def to_jsonable(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, BaseModel):
        return value.model_dump()
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return str(value)


def print_result(payload: dict) -> None:
    print(json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False))


def study_insurance_triage(email_id: str = "CLN-001") -> dict:
    memory = new_thread("insurance")
    fnol = insurance.fnol_lookup(email_id)
    append_tool(memory, "fnol_lookup")

    claim_id = fnol.get("claim_id") or fnol.get("claim_number_ground_truth", "")
    policy_id = fnol.get("policy_id") or fnol.get("policy_id_ground_truth", "")
    claim = insurance.claim_lookup(claim_id) if claim_id else {"found": False}
    policy = insurance.policy_lookup(policy_id) if policy_id else {"found": False}
    append_tool(memory, "claim_lookup")
    append_tool(memory, "policy_lookup")

    evidence = {
        "email_id": email_id,
        "claim_id": claim_id,
        "policy_id": policy_id,
        "fnol": fnol,
        "claim": claim,
        "policy": policy,
    }

    decision = TriageDecision(
        lane="insurance",
        case_id=email_id,
        urgency="medium",
        route_queue="fnol_intake",
        summary="Study-path triage using tool evidence.",
        rationale="FNOL, claim, and policy lookups completed.",
        tools_used=memory.tool_trace,
        confidence=0.9,
        needs_human_approval=False,
    )
    outcome = validate_decision(decision, evidence)
    handoff = build_handoff(decision) if outcome.status == "completed" else None
    return {
        "memory": memory,
        "evidence": evidence,
        "outcome": outcome,
        "handoff": handoff,
        "agent_paths": {
            "langgraph": langgraph_triage.__name__,
            "sdk": sdk_assistant.__name__,
        },
        "model": config.DEFAULT_MODEL,
    }


def study_hold_release(container_id: str, *, approved: bool, key: str) -> dict:
    shipment = logistics.shipment_lookup(container_id)
    allowed = can_run_write(
        tool_name="release_hold",
        approved=approved,
        idempotency_key=key,
    )
    if not allowed:
        return {
            "shipment": shipment,
            "status": "blocked",
            "reason": "Write requires approval and idempotency key.",
        }
    return {
        "shipment": shipment,
        "status": "ok",
        "result": logistics.release_hold(container_id, key),
    }


if __name__ == "__main__":
    print("Study entry only. Prefer Day 1 demonstration notebooks.")
    print_result(study_insurance_triage("CLN-001"))
