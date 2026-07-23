"""Day 2 -- wraps yesterday's resolve_email with urgency classification,
a deterministic authorization gate, and an independent second grounding
check via the Day 2 network-MCP and A2A lookup logic.

  1. Call app.my_day1_resolve.resolve_email unchanged -- get claim_id + grounding.
  2. If a claim_id was found, classify urgency: exactly one Bedrock Converse
     call if AWS_BEARER_TOKEN_BEDROCK and BEDROCK_MODEL_ID are BOTH set
     (urgency_source="bedrock"); otherwise a clearly-labeled deterministic
     stub (urgency_source="stub-no-credentials") so the pipeline stays
     runnable without live AWS access.
  3. Run that urgency through a deterministic authorization gate written in
     plain code -- the model's label only ever informs the decision, code
     decides the action.
  4. Independently re-confirm grounding by calling, in-process, the plain
     lookup functions behind this afternoon's network-MCP server
     (W2D2/my_claims_network_server.py) and A2A server
     (W2D2/my_a2a_claims_server.py) -- a second, separate check, not a
     second walk through step 1's own lookup path.

Run it:
    uv run python -m app.my_day2_resolve CLN-001
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

from app.my_day1_resolve import CLAIMS_DB
from app.my_day1_resolve import resolve_email as day1_resolve_email

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "W2D2"))
from my_a2a_claims_server import lookup_claim_status  # noqa: E402
from my_claims_network_server import lookup_claim_and_policy as network_lookup_claim_and_policy  # noqa: E402

AWS_REGION = "us-east-1"

USING_LIVE_BEDROCK = bool(os.environ.get("AWS_BEARER_TOKEN_BEDROCK")) and bool(os.environ.get("BEDROCK_MODEL_ID"))


def _lookup_claim_basics(claim_id: str) -> dict[str, object]:
    connection = sqlite3.connect(CLAIMS_DB)
    try:
        row = connection.execute(
            "SELECT claim_id, loss_type, reserve_usd, route_queue FROM claims WHERE claim_id = ?",
            (claim_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        raise ValueError(f"claim_id {claim_id!r} was not found.")
    claim_id_out, loss_type, reserve_usd, route_queue = row
    return {"claim_id": claim_id_out, "loss_type": loss_type, "reserve_usd": reserve_usd, "route_queue": route_queue}


def classify_urgency_bedrock(claim: dict[str, object], model_id: str) -> str:
    """One bounded Converse call -- classification only, no write action."""
    import boto3  # imported lazily so the rest of this module works without boto3 installed

    client = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION)
    prompt = (
        f"Claim {claim['claim_id']}, loss_type={claim['loss_type']}, "
        f"reserve_usd={claim['reserve_usd']}. Reply with exactly one word: "
        "LOW, MEDIUM, or HIGH urgency."
    )
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 10, "temperature": 0},
    )
    text = response["output"]["message"]["content"][0]["text"].strip().upper()
    if text not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError(f"Bedrock returned an unexpected urgency label: {text!r}")
    return text


def _stub_urgency(reserve_usd: float) -> str:
    """Deterministic, clearly-labeled stand-in for the Bedrock call -- same
    shape of decision (LOW/MEDIUM/HIGH), zero model calls, used only when
    live Bedrock credentials aren't configured in this environment."""
    if reserve_usd > 50_000:
        return "HIGH"
    if reserve_usd > 10_000:
        return "MEDIUM"
    return "LOW"


def deterministic_authorization_gate(claim: dict[str, object], model_urgency: str) -> str:
    """The model classifies; code -- not the model -- decides what happens next."""
    if claim["reserve_usd"] > 100_000:
        return "escalate_to_human — high reserve amount, model output is advisory only"
    if model_urgency.upper() == "HIGH":
        return "route_to_priority_queue"
    return "route_to_standard_queue"


def resolve_email(email_id: str) -> dict[str, object]:
    result = day1_resolve_email(email_id)
    claim_id = result.get("claim_id")
    if not claim_id:
        return result

    claim = _lookup_claim_basics(claim_id)

    if USING_LIVE_BEDROCK:
        model_id = os.environ["BEDROCK_MODEL_ID"]
        urgency = classify_urgency_bedrock(claim, model_id)
        result["urgency_source"] = "bedrock"
    else:
        urgency = _stub_urgency(claim["reserve_usd"])
        result["urgency_source"] = "stub-no-credentials"
    result["model_urgency"] = urgency
    result["authorization_decision"] = deterministic_authorization_gate(claim, urgency)

    result["network_grounding_check"] = network_lookup_claim_and_policy(claim_id).model_dump()
    result["a2a_status_check"] = lookup_claim_status(claim_id)
    return result


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
