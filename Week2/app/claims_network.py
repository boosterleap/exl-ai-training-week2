"""Day 2 -- standalone network MCP server (Streamable HTTP).

Adapted from W2D2/snippets/claims_network_server.py. Contrast with Day 1's
claims_lookup.py: that one is in-process (stdio), launched by Claude Code
itself. This one is a real network service you start in a separate
terminal -- the exercise is the network round trip itself, so this file
stays a standalone process rather than something day2_resolve.py spawns.

Run it:
    uv run python -m app.claims_network
Endpoint: http://127.0.0.1:8766/mcp
"""

from __future__ import annotations

import sqlite3

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict

from app.paths import CLAIMS_DB, POLICIES_DIR, PRODUCT_TO_POLICY_PREFIX

mcp = FastMCP(
    "claims-network",
    instructions="Read-only network lookup for claims and grounding policy docs.",
    host="127.0.0.1",
    port=8766,
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


class ClaimGroundingStatus(BaseModel):
    """Deliberately narrower than app.models.ClaimAndPolicy -- this network
    tool only needs to answer "is this claim grounded", not the full record."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim_status: str
    product: str
    grounding_available: bool
    policy_doc_files: list[str]


def get_claim_grounding_status(claim_id: str) -> ClaimGroundingStatus:
    """Plain function -- the seam day2_resolve.py calls in-process."""
    connection = sqlite3.connect(CLAIMS_DB)
    try:
        row = connection.execute(
            """
            SELECT claims.claim_id, claims.status, policies.product
            FROM claims JOIN policies ON claims.policy_id = policies.policy_id
            WHERE claims.claim_id = ?
            """,
            (claim_id.strip().upper(),),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        raise ValueError(f"claim_id {claim_id!r} was not found.")

    claim_id_out, status, product = row
    prefix = PRODUCT_TO_POLICY_PREFIX.get(product)
    doc_files = sorted(p.name for p in POLICIES_DIR.glob(f"{prefix}_*.md")) if prefix else []
    return ClaimGroundingStatus(
        claim_id=claim_id_out,
        claim_status=status,
        product=product,
        grounding_available=bool(doc_files),
        policy_doc_files=doc_files,
    )


@mcp.tool()
def get_claim_and_policy(claim_id: str) -> ClaimGroundingStatus:
    """Look up a claim and which policy documents (if any) ground it, over the network."""
    return get_claim_grounding_status(claim_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
