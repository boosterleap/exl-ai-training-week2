"""Day 2 -- standalone network MCP server (Streamable HTTP).

Exposes get_claim_and_policy the same way Day 1's insurance-lookup tool
(app/claims_lookup.py) did -- same full ClaimAndPolicy record, same
grounding logic -- but as a real network service instead of an
in-process (stdio) server Claude Code launches itself.

Run it (separate terminal):
    uv run python W2D2/my_claims_network_server.py
Endpoint: http://127.0.0.1:8766/mcp
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# product -> policy document prefix under data/insurance/policies/.
# "commercial_package" has NO entry on purpose -- see data/_DATA_README.md.
PRODUCT_TO_POLICY_PREFIX: dict[str, str] = {
    "homeowners": "POL-HOME-010",
    "auto": "POL-AUTO-001",
    "commercial_property": "POL-COMM-030",
    "landlord_liability": "POL-LL-040",
    "health": "POL-HEALTH-020",
}


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
CLAIMS_DB = REPO_ROOT / "data" / "insurance" / "claims.db"
POLICIES_DIR = REPO_ROOT / "data" / "insurance" / "policies"

mcp = FastMCP(
    "claims-network",
    instructions=(
        "Read-only network lookup for insurance claims, policies, and their "
        "grounding policy documents. Never invents a claim, policy, or "
        "document that does not exist in the underlying data."
    ),
    host="127.0.0.1",
    port=8766,
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


class ClaimAndPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim_status: str
    loss_type: str
    urgency: str
    reserve_usd: float
    route_queue: str
    policy_id: str
    named_insured: str
    policy_status: str
    product: str
    grounding_available: bool
    policy_doc_files: list[str] = Field(default_factory=list)


def lookup_claim_and_policy(claim_id: str) -> ClaimAndPolicy:
    """Plain function (no MCP transport) -- mirrors app/claims_lookup.py."""
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
        "server": "claims-network",
        "transport": "streamable-http",
        "endpoint": "http://127.0.0.1:8766/mcp",
        "claims_db": str(CLAIMS_DB),
        "sample_lookup": sample.model_dump(),
        "deliberate_gap_lookup": ungrounded.model_dump(),
    }


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        import json

        print(json.dumps(self_check(), indent=2))
    else:
        mcp.run(transport="streamable-http")
