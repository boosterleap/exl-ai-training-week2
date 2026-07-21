"""Day 2 -- adds a triage/grounding handoff on top of Day 1.

day1_resolve gave a single agent doing everything in one pass. This stage
splits that into two roles and has them hand off:

  1. Triage: classify urgency (via Bedrock if AWS_BEARER_TOKEN_BEDROCK and
     BEDROCK_MODEL_ID are set; otherwise a clearly-labeled stub so the
     pipeline stays runnable without live AWS access) and run it through a
     deterministic authorization gate -- the model never decides the
     action, only informs it.
  2. Grounding: independently re-confirm the claim is grounded via the
     Day 2 network-MCP and A2A lookup *logic* (called in-process here; the
     standalone claims_network.py / claims_a2a.py servers are the real
     network/A2A exercise, started separately -- see the session guide).

Run it:
    uv run python -m app.day2_resolve CLN-001
"""

from __future__ import annotations

import json
import os
import sys

from app.bedrock_urgency import classify_urgency, deterministic_authorization_gate
from app.bedrock_urgency import lookup_claim as bedrock_lookup_claim
from app.claims_a2a import lookup_status
from app.claims_network import get_claim_grounding_status
from app.day1_resolve import resolve_email as day1_resolve_email

USING_LIVE_BEDROCK = bool(os.environ.get("AWS_BEARER_TOKEN_BEDROCK")) and bool(os.environ.get("BEDROCK_MODEL_ID"))


def _stub_urgency(reserve_usd: float) -> str:
    """Deterministic, clearly-labeled stand-in for the Bedrock call -- same
    shape of decision (LOW/MEDIUM/HIGH), zero model calls, used only when
    live Bedrock credentials aren't configured in this environment."""
    if reserve_usd > 50_000:
        return "HIGH"
    if reserve_usd > 10_000:
        return "MEDIUM"
    return "LOW"


def resolve_email(email_id: str) -> dict[str, object]:
    result = day1_resolve_email(email_id)
    claim_id = result.get("claim_id")
    if not claim_id:
        return result

    bedrock_claim = bedrock_lookup_claim(claim_id)
    if USING_LIVE_BEDROCK:
        model_id = os.environ["BEDROCK_MODEL_ID"]
        urgency = classify_urgency(bedrock_claim, model_id)
        result["urgency_source"] = "bedrock"
    else:
        urgency = _stub_urgency(bedrock_claim["reserve_usd"])
        result["urgency_source"] = "stub-no-credentials"
    result["model_urgency"] = urgency
    result["authorization_decision"] = deterministic_authorization_gate(bedrock_claim, urgency)

    result["network_grounding_check"] = get_claim_grounding_status(claim_id).model_dump()
    result["a2a_status_check"] = lookup_status(claim_id)
    return result


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
