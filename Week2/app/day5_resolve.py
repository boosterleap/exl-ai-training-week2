"""Day 5 -- the capstone increment: audit every decision, gate on the
declared autonomy level, and run the whole inbox end to end.

Every resolve_email call is gated by the real claims-triage governance
entry (data/governance/use_case_risk_tiers.json: high risk tier,
"recommend" autonomy -- never "act") and logged to a persisted,
tamper-evident audit chain. resolve_all() runs the complete FNOL inbox
(all 12 rows in data/insurance/fnol_emails.csv) through the full Day
1-5 pipeline and reports a summary.

Run it:
    uv run python -m app.day5_resolve CLN-001
    uv run python -m app.day5_resolve --resolve-all
"""

from __future__ import annotations

import csv
import json
import sys

from app.audit_chain import AuditChain
from app.autonomy_check import check_use_case, claims_triage_use_case
from app.day4_resolve import resolve_email as day4_resolve_email
from app.paths import FNOL_EMAILS_CSV

_chain: AuditChain | None = None


def _get_chain() -> AuditChain:
    global _chain
    if _chain is None:
        _chain = AuditChain.load_from()
    return _chain


def _autonomy_gate() -> dict:
    use_case = claims_triage_use_case()
    check = check_use_case(use_case)
    if not check["within_bounds"]:
        raise RuntimeError(
            f"claims-triage autonomy ({use_case['autonomy']}) exceeds what its risk tier "
            f"({use_case['tier']}) allows -- refusing to run until governance approves a change."
        )
    return check


def resolve_email(email_id: str) -> dict[str, object]:
    autonomy = _autonomy_gate()
    chain = _get_chain()
    result = day4_resolve_email(email_id)

    fraud_signal = result.get("fraud_signal")
    event = {
        "email_id": email_id,
        "claim_id": result.get("claim_id"),
        "escalate": result.get("escalate"),
        "injection_blocked": result.get("injection_blocked", False),
        "model_urgency": result.get("model_urgency"),
        "authorization_decision": result.get("authorization_decision"),
        "fraud_flag": fraud_signal["flag"] if fraud_signal else None,
        "autonomy_level": autonomy["autonomy"],
        "autonomy_within_bounds": autonomy["within_bounds"],
    }
    record = chain.append(event)
    chain.persist_to()
    result["audit_record_hash"] = record["hash"]
    result["audit_chain_valid"] = chain.verify()
    return result


def resolve_all() -> tuple[list[dict], dict]:
    with FNOL_EMAILS_CSV.open(newline="", encoding="utf-8") as f:
        email_ids = [row["email_id"] for row in csv.DictReader(f)]
    results = [resolve_email(eid) for eid in email_ids]
    summary = {
        "total": len(results),
        "grounded_replies": sum(1 for r in results if r.get("found") and not r.get("escalate") and not r.get("injection_blocked")),
        "escalated": sum(1 for r in results if r.get("escalate")),
        "injection_blocked": sum(1 for r in results if r.get("injection_blocked")),
        "audit_chain_valid": _get_chain().verify(),
        "audit_entries": len(_get_chain().entries),
    }
    return results, summary


def main() -> None:
    if "--resolve-all" in sys.argv:
        _, summary = resolve_all()
        print(json.dumps(summary, indent=2))
    else:
        email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
        print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
