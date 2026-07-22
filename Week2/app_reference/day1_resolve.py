"""Day 1 -- the seed of the progressive app: resolve_email(email_id).

Reads one inbound FNOL email, looks up its claim + policy via the Day 1
stdio MCP tool's underlying lookup function, and drafts a grounded reply --
or escalates instead of guessing when there's nothing to ground on (the
commercial_package gap, or an email with no claim number at all).

Run it:
    uv run python -m app.day1_resolve CLN-001
"""

from __future__ import annotations

import csv
import json
import sys

from app.claims_lookup import lookup_claim_and_policy
from app.paths import FNOL_EMAILS_CSV


def load_email(email_id: str) -> dict[str, str]:
    with FNOL_EMAILS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["email_id"] == email_id:
                return row
    raise ValueError(f"email_id {email_id!r} not found in {FNOL_EMAILS_CSV.name}")


def resolve_email(email_id: str) -> dict[str, object]:
    email = load_email(email_id)
    claim_id = email["claim_number_ground_truth"].strip()
    result: dict[str, object] = {
        "email_id": email_id,
        "subject": email["subject"],
        "category": email["email_category"],
        "claim_id": claim_id or None,
    }

    if not claim_id:
        result.update(
            found=False,
            escalate=True,
            escalate_reason=(
                f"No claim number in this email (category={email['email_category']!r}) -- "
                f"route to {email['route_queue_ground_truth']} for human handling."
            ),
            draft_reply=None,
        )
        return result

    try:
        claim = lookup_claim_and_policy(claim_id)
    except ValueError as exc:
        result.update(found=False, escalate=True, escalate_reason=str(exc), draft_reply=None)
        return result

    result["found"] = True
    result["claim"] = claim.model_dump()

    if not claim.grounding_available:
        result["escalate"] = True
        result["escalate_reason"] = (
            f"No policy document exists for product={claim.product!r} -- cannot ground "
            "a coverage statement. Escalate to a human adjuster rather than answer from "
            "general knowledge."
        )
        result["draft_reply"] = None
        return result

    result["escalate"] = False
    result["escalate_reason"] = None
    result["draft_reply"] = (
        f"Thank you for reporting claim {claim.claim_id} under policy {claim.policy_id} "
        f"({claim.named_insured}). Status: {claim.claim_status}. This has been routed to "
        f"{claim.route_queue}. Coverage will be assessed against "
        f"{', '.join(claim.policy_doc_files)}."
    )
    return result


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
