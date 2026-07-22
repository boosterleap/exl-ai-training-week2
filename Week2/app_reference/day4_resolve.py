"""Day 4 -- wraps Day 3 with guardrails on the raw inbound email.

Before any claim lookup or tool call happens, the raw email body is:
  1. scanned for prompt-injection patterns -- if flagged, the pipeline
     stops immediately and escalates, without ever calling a lookup tool
     on attacker-controlled input;
  2. PII-redacted for safe logging (the redacted version is what gets
     attached to the result / later audit trail -- never the raw body).

Run it:
    uv run python -m app.day4_resolve CLN-001
"""

from __future__ import annotations

import json
import sys

from app.day1_resolve import load_email
from app.day3_resolve import resolve_email as day3_resolve_email
from app.injection_scanner import scan
from app.pii_guardrail import AnonymizerEngine, build_analyzer, redact

_analyzer = None
_anonymizer = None


def _get_guardrail_engines():
    global _analyzer, _anonymizer
    if _analyzer is None:
        _analyzer = build_analyzer()
        _anonymizer = AnonymizerEngine()
    return _analyzer, _anonymizer


def resolve_email(email_id: str) -> dict[str, object]:
    email = load_email(email_id)
    body = email["body"]

    if scan(body):
        return {
            "email_id": email_id,
            "subject": email["subject"],
            "category": email["email_category"],
            "claim_id": None,
            "found": False,
            "injection_blocked": True,
            "escalate": True,
            "escalate_reason": "Inbound email body matched a prompt-injection pattern -- blocked before any tool call.",
            "draft_reply": None,
        }

    analyzer, anonymizer = _get_guardrail_engines()
    redacted_body, pii_findings = redact(body, analyzer, anonymizer)

    result = day3_resolve_email(email_id)
    result["injection_blocked"] = False
    result["redacted_body"] = redacted_body
    result["pii_findings"] = pii_findings
    return result


def main() -> None:
    email_id = sys.argv[1] if len(sys.argv) > 1 else "CLN-001"
    print(json.dumps(resolve_email(email_id), indent=2))


if __name__ == "__main__":
    main()
