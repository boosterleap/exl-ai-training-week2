"""Day 1 — in-process (stdio) MCP tool: grounded claim + policy lookup.

Adapted from W2D1/snippets/insurance_lookup_server.py for the progressive
app: same lookup logic, now importing the shared app.paths / app.models
instead of redefining them locally.

Run as an MCP server (what Claude Code launches as a subprocess):
    uv run python app/claims_lookup.py
Run a syntax/self-check directly:
    uv run python app/claims_lookup.py --self-check
"""

from __future__ import annotations

import sqlite3
import sys

from mcp.server.fastmcp import FastMCP

from app.models import ClaimAndPolicy
from app.paths import CLAIMS_DB, POLICIES_DIR, PRODUCT_TO_POLICY_PREFIX

mcp = FastMCP(
    "insurance-lookup",
    instructions=(
        "Read-only lookup for insurance claims, policies, and their grounding "
        "policy documents. Never invents a claim, policy, or document that "
        "does not exist in the underlying data."
    ),
)


def lookup_claim_and_policy(claim_id: str) -> ClaimAndPolicy:
    """Plain function (no MCP transport) -- the seam day2_resolve.py and later import."""
    if not CLAIMS_DB.is_file():
        raise FileNotFoundError(f"claims.db not found at {CLAIMS_DB}")
    connection = sqlite3.connect(CLAIMS_DB)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT claims.claim_id, claims.status, claims.loss_type, claims.urgency,
                   claims.reserve_usd, claims.route_queue,
                   policies.policy_id, policies.named_insured, policies.status,
                   policies.product
            FROM claims JOIN policies ON claims.policy_id = policies.policy_id
            WHERE claims.claim_id = ?
            """,
            (claim_id,),
        )
        row = cursor.fetchone()
    finally:
        connection.close()

    if row is None:
        raise ValueError(f"claim_id {claim_id!r} was not found in claims.db.")

    (
        claim_id_out, claim_status, loss_type, urgency, reserve_usd, route_queue,
        policy_id, named_insured, policy_status, product,
    ) = row

    prefix = PRODUCT_TO_POLICY_PREFIX.get(product)
    doc_files: list[str] = []
    if prefix:
        doc_files = sorted(p.name for p in POLICIES_DIR.glob(f"{prefix}_*.md"))

    return ClaimAndPolicy(
        claim_id=claim_id_out,
        claim_status=claim_status,
        loss_type=loss_type,
        urgency=urgency,
        reserve_usd=reserve_usd,
        route_queue=route_queue,
        policy_id=policy_id,
        named_insured=named_insured,
        policy_status=policy_status,
        product=product,
        grounding_available=bool(doc_files),
        policy_doc_files=doc_files,
    )


@mcp.tool()
def get_claim_and_policy(claim_id: str) -> ClaimAndPolicy:
    """Look up a claim, its policy, and which policy documents (if any) ground it.

    If grounding_available is false, no policy document exists for this
    product -- do not answer a coverage question from general knowledge;
    escalate instead.
    """
    normalized = claim_id.strip().upper()
    if not normalized:
        raise ValueError("claim_id must be a non-empty claim ID, e.g. CLM-424063.")
    return lookup_claim_and_policy(normalized)


def self_check() -> dict[str, object]:
    sample = lookup_claim_and_policy("CLM-424063")
    ungrounded = lookup_claim_and_policy("CLM-255335")
    return {
        "ok": True,
        "server": "insurance-lookup",
        "transport": "stdio",
        "claims_db": str(CLAIMS_DB),
        "sample_lookup": sample.model_dump(),
        "deliberate_gap_lookup": ungrounded.model_dump(),
    }


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        import json

        print(json.dumps(self_check(), indent=2))
    else:
        mcp.run()
