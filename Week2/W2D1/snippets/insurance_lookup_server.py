"""Reference MCP server for the Day 1 PM lookup tool exercise.

This is a fallback/reference implementation — the session guide (index.html)
asks you to have Claude Code DESIGN and BUILD this tool with you rather than
copy this file verbatim. Use this only if your own build gets stuck, or to
compare against what you built.

Local, in-process (stdio) MCP server: Claude Code launches this script itself
as a subprocess per data/_DATA_README.md's product -> policy-doc mapping.
No network port, no separate terminal needed (contrast with the Day 2 PM
Streamable HTTP MCP server, which *is* a standalone network service).

Run a syntax/self-check directly:
    uv run python W2D1/snippets/insurance_lookup_server.py --self-check
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

# product -> policy document prefix under data/insurance/policies/.
# "commercial_package" has NO entry on purpose — see data/_DATA_README.md.
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
    "insurance-lookup",
    instructions=(
        "Read-only lookup for insurance claims, policies, and their grounding "
        "policy documents. Never invents a claim, policy, or document that "
        "does not exist in the underlying data."
    ),
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


def _lookup(claim_id: str) -> ClaimAndPolicy:
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
    product — do not answer a coverage question from general knowledge;
    escalate instead.
    """
    normalized = claim_id.strip().upper()
    if not normalized:
        raise ValueError("claim_id must be a non-empty claim ID, e.g. CLM-424063.")
    return _lookup(normalized)


def self_check() -> dict[str, object]:
    sample = _lookup("CLM-424063")
    ungrounded = _lookup("CLM-255335")
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
