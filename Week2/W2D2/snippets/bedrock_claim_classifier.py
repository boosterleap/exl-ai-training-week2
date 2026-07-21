"""Reference bounded Bedrock gateway call for the Day 2 PM AWS topic.

Fallback/reference only — the session guide asks you to have Claude Code
adapt this with the exact model ID your sandbox approves. Makes exactly
ONE Converse call, classifies one claim's urgency, and applies a
deterministic (non-model) authorization check before "approving" anything
— the model's opinion is never the authorization decision (see Topic 04's
trust-boundary concept).

Auth: set AWS_BEARER_TOKEN_BEDROCK (an Amazon Bedrock API key, generated
in the AWS Bedrock console under API keys) as an environment variable
before running this — see the collapsible AWS setup guide in the session
page for the exact console steps. Do not hardcode the key in this file.

Run it:
    uv run python W2D2/snippets/bedrock_claim_classifier.py CLM-424063
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import boto3

AWS_REGION = "us-east-1"


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


def lookup_claim(claim_id: str) -> dict:
    db = discover_repo_root() / "data" / "insurance" / "claims.db"
    connection = sqlite3.connect(db)
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
    """One bounded Converse call — classification only, no write action."""
    if "AWS_BEARER_TOKEN_BEDROCK" not in os.environ:
        raise RuntimeError(
            "AWS_BEARER_TOKEN_BEDROCK is not set. Generate a Bedrock API key in the "
            "AWS console (Bedrock -> API keys) and export it first."
        )
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
    return response["output"]["message"]["content"][0]["text"].strip()


def deterministic_authorization_gate(claim: dict, model_urgency: str) -> str:
    """The model classifies; code — not the model — decides what happens next."""
    if claim["reserve_usd"] > 100_000:
        return "escalate_to_human — high reserve amount, model output is advisory only"
    if model_urgency.upper() == "HIGH":
        return "route_to_priority_queue"
    return "route_to_standard_queue"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python bedrock_claim_classifier.py <claim_id>")
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
