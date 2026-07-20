"""Evidence checks before accepting a TriageDecision."""

from __future__ import annotations

from ..models import TriageDecision, TriageOutcome


REQUIRED_INSURANCE_KEYS = {"email_id", "claim_id", "policy_id"}


def has_insurance_evidence(evidence: dict) -> bool:
    return REQUIRED_INSURANCE_KEYS.issubset(evidence.keys()) and all(
        evidence.get(key) for key in REQUIRED_INSURANCE_KEYS
    )


def validate_decision(decision: TriageDecision, evidence: dict) -> TriageOutcome:
    if decision.lane == "insurance" and not has_insurance_evidence(evidence):
        return TriageOutcome(
            status="refused",
            refusal_reason="Missing FNOL, claim, or policy evidence.",
        )
    if decision.confidence < 0.5:
        return TriageOutcome(
            status="refused",
            refusal_reason="Confidence below acceptance threshold.",
        )
    return TriageOutcome(status="completed", decision=decision)
