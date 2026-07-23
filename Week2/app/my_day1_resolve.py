"""Day 1 -- resolve_email(email_id): read an inbound FNOL email, look up its
claim + policy via the same lookup the insurance-lookup MCP tool exposes
(get_claim_and_policy), and draft a grounded reply -- or escalate instead of
guessing when there's nothing to ground on (no claim number in the email,
or no policy document for that product).

Run it:
    uv run python -m app.my_day1_resolve CLN-001
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
CLAIMS_DB = REPO_ROOT / "data" / "insurance" / "claims.db"
POLICIES_DIR = REPO_ROOT / "data" / "insurance" / "policies"
FNOL_EMAILS_CSV = REPO_ROOT / "data" / "insurance" / "fnol_emails.csv"

# product -> policy document prefix under data/insurance/policies/.
# "commercial_package" has NO entry on purpose -- see data/_DATA_README.md.
PRODUCT_TO_POLICY_PREFIX: dict[str, str] = {
    "homeowners": "POL-HOME-010",
    "auto": "POL-AUTO-001",
    "commercial_property": "POL-COMM-030",
    "landlord_liability": "POL-LL-040",
    "health": "POL-HEALTH-020",
}


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


def get_claim_and_policy(claim_id: str) -> ClaimAndPolicy:
    """Same lookup logic as the insurance-lookup MCP tool (W2D1/snippets/insurance_lookup_server.py)."""
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


def load_email(email_id: str) -> dict[str, str]:
    with FNOL_EMAILS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["email_id"] == email_id:
                return row
    raise ValueError(f"email_id {email_id!r} not found in {FNOL_EMAILS_CSV.name}")


def resolve_email(email_id: str) -> dict[str, object]:
    try:
        email = load_email(email_id)
    except ValueError as exc:
        return {
            "email_id": email_id,
            "claim_id": None,
            "found": False,
            "escalate": True,
            "escalate_reason": str(exc),
            "draft_reply": None,
        }
    claim_id = email["claim_number_ground_truth"].strip()

    if not claim_id:
        return {
            "email_id": email_id,
            "claim_id": None,
            "found": False,
            "escalate": True,
            "escalate_reason": (
                f"No claim number in this email (category={email['email_category']!r}) -- "
                "cannot look up a claim without one; route to a human for intake."
            ),
            "draft_reply": None,
        }

    claim = get_claim_and_policy(claim_id)

    if not claim.grounding_available:
        return {
            "email_id": email_id,
            "claim_id": claim_id,
            "found": True,
            "escalate": True,
            "escalate_reason": (
                f"No policy document exists for product={claim.product!r} -- cannot ground "
                "a coverage statement. Escalate to a human adjuster rather than answer from "
                "general knowledge."
            ),
            "draft_reply": None,
        }

    return {
        "email_id": email_id,
        "claim_id": claim_id,
        "found": True,
        "escalate": False,
        "escalate_reason": None,
        "draft_reply": (
            f"Thank you for reporting claim {claim.claim_id} under policy {claim.policy_id} "
            f"({claim.named_insured}). Status: {claim.claim_status}. This has been routed to "
            f"{claim.route_queue}. Coverage will be assessed against "
            f"{', '.join(claim.policy_doc_files)}."
        ),
    }


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
