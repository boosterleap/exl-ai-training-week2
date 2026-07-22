"""Day 2 -- bounded Bedrock urgency classification, adapted from
W2D2/snippets/bedrock_claim_classifier.py.

Makes exactly ONE Converse call, classifies one claim's urgency, and
applies a deterministic (non-model) authorization check before "approving"
anything -- the model's opinion is never the authorization decision.

Auth: set AWS_BEARER_TOKEN_BEDROCK (an Amazon Bedrock API key) and
BEDROCK_MODEL_ID before calling classify_urgency() for real. Without
them, day2_resolve.py falls back to a clearly-labeled stub urgency so the
rest of the pipeline stays runnable without live AWS access -- see
day2_resolve.py's USING_LIVE_BEDROCK flag.

Run it directly:
    uv run python -m app.bedrock_urgency CLM-424063
"""

from __future__ import annotations

import os
import sqlite3
import sys

from app.paths import CLAIMS_DB

AWS_REGION = "us-east-1"


def lookup_claim(claim_id: str) -> dict:
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


def classify_urgency(claim: dict, model_id: str) -> str:
    """One bounded Converse call -- classification only, no write action."""
    if "AWS_BEARER_TOKEN_BEDROCK" not in os.environ:
        raise RuntimeError(
            "AWS_BEARER_TOKEN_BEDROCK is not set. Generate a Bedrock API key in the "
            "AWS console (Bedrock -> API keys) and export it first."
        )
    import boto3  # imported lazily so the rest of this module works without boto3 installed

    client = boto3.client(service_name="bedrock-runtime", region_name=AWS_REGION)
    prompt = (
        f"Claim {claim['claim_id']}, loss_type={claim['loss_type']}, "
        f"reserve_usd={claim['reserve_usd']}. Reply with exactly one word: "
        f"LOW, MEDIUM, or HIGH urgency."
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


def deterministic_authorization_gate(claim: dict, model_urgency: str) -> str:
    """The model classifies; code -- not the model -- decides what happens next."""
    if claim["reserve_usd"] > 100_000:
        return "escalate_to_human — high reserve amount, model output is advisory only"
    if model_urgency.upper() == "HIGH":
        return "route_to_priority_queue"
    return "route_to_standard_queue"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.bedrock_urgency <claim_id>")
        sys.exit(1)
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if not model_id:
        raise RuntimeError("Set BEDROCK_MODEL_ID to the exact sandbox-approved model ID first.")
    claim = lookup_claim(sys.argv[1])
    urgency = classify_urgency(claim, model_id)
    decision = deterministic_authorization_gate(claim, urgency)
    print({"claim": claim, "model_urgency": urgency, "authorization_decision": decision})


if __name__ == "__main__":
    main()
