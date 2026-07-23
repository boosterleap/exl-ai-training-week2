"""Guardrails AI variant of pii_guardrail.py, for comparison only.

Same redact(text) -> (redacted_text, findings) contract as pii_guardrail.py,
but backed by the Guardrails AI `DetectPII` validator (guardrails.hub)
instead of calling Presidio directly. DetectPII itself runs Presidio under
the hood, so detection quality is expected to match pii_guardrail.py --
the difference under test here is the Guardrails AI wrapper/on_fail="fix"
mechanics, not a different detection engine.

Requires (one-time, needs GUARDRAILS_API_KEY -- NOT fully local like
pii_guardrail.py):
    uv pip install --python <venv> guardrails-ai
    <venv>/Scripts/guardrails.exe configure --token $GUARDRAILS_API_KEY --disable-metrics
    <venv>/Scripts/guardrails.exe hub install hub://guardrails/detect_pii

Run it:
    uv run --python <venv> python W2D4/snippets/pii_guardrail_guardrails_ai.py
"""

from __future__ import annotations

from guardrails import Guard
from guardrails.hub import DetectPII

PII_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "LOCATION",
    "US_DRIVER_LICENSE",
    "DATE_TIME",
]


def build_guard() -> Guard:
    validator = DetectPII(pii_entities=PII_ENTITIES, on_fail="fix")
    return Guard().use(validator)


def redact(text: str, guard: Guard) -> tuple[str, list[dict]]:
    """Returns (redacted_text, findings). validation_passed is True even when
    PII was found, because on_fail="fix" resolves the failure -- so whether
    PII was found is read from the validator's error_spans instead."""
    outcome = guard.validate(text)
    redacted = outcome.validated_output if outcome.validated_output else text

    findings: list[dict] = []
    last_call = guard.history.last
    if last_call is not None:
        logs = last_call.iterations.last.outputs.validator_logs
        for log in logs:
            result = log.validation_result
            spans = getattr(result, "error_spans", None) or []
            for span in spans:
                findings.append({"reason": span.reason, "text": text[span.start : span.end]})

    return redacted, findings


if __name__ == "__main__":
    import csv
    from pathlib import Path

    guard = build_guard()

    sample = (
        "Please contact Jennifer Garcia at jennifer.garcia@example.com or "
        "555-123-4567 about claim CLM-424063."
    )
    redacted, findings = redact(sample, guard)
    print("=== Sample text ===")
    print("Original: ", sample)
    print("Redacted: ", redacted)
    print("Findings:")
    for f in findings:
        print(f"  {f['reason']:35s} {f['text']!r}")

    repo_root = Path(__file__).resolve().parents[2]
    csv_path = repo_root / "data" / "insurance" / "fnol_emails.csv"
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["email_id"] == "CLN-001":
                body = row["body"]
                break

    redacted, findings = redact(body, guard)
    print("\n=== CLN-001 body ===")
    print("Original: ", body)
    print("Redacted: ", redacted)
    print("Findings:")
    for f in findings:
        print(f"  {f['reason']:35s} {f['text']!r}")
