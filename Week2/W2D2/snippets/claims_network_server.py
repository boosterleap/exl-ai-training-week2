"""Reference network MCP server for the Day 2 PM MCP-in-depth topic.

Fallback/reference only — the session guide asks you to have Claude Code
build this with you. Contrast with Day 1's insurance_lookup_server.py:
that one is in-process (stdio), launched by Claude Code itself. This one
is a standalone network service (Streamable HTTP) you start yourself in
a separate terminal, the same pattern as mcp_servers/inventory_server.py
in the original curriculum reference.

Run it:
    uv run python W2D2/snippets/claims_network_server.py
Endpoint: http://127.0.0.1:8766/mcp
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict

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
    instructions="Read-only network lookup for claims and grounding policy docs.",
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
    product: str
    grounding_available: bool
    policy_doc_files: list[str]


@mcp.tool()
def get_claim_and_policy(claim_id: str) -> ClaimAndPolicy:
    """Look up a claim and which policy documents (if any) ground it, over the network."""
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
    return ClaimAndPolicy(
        claim_id=claim_id_out,
        claim_status=status,
        product=product,
        grounding_available=bool(doc_files),
        policy_doc_files=doc_files,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
