"""Contract tests for the Day 1 study app models."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app.models import TriageDecision, TriageOutcome  # noqa: E402


def test_completed_outcome_requires_valid_decision() -> None:
    with pytest.raises(ValidationError):
        TriageOutcome(status="completed")


def test_refusal_requires_visible_reason() -> None:
    with pytest.raises(ValidationError):
        TriageOutcome(status="refused")


def test_valid_refusal_contains_no_fabricated_decision() -> None:
    outcome = TriageOutcome(
        status="refused",
        refusal_reason="No authoritative FNOL record was returned.",
    )
    assert outcome.decision is None


def test_valid_completed_decision() -> None:
    decision = TriageDecision(
        lane="insurance",
        case_id="CLN-001",
        urgency="high",
        route_queue="fnol_intake",
        summary="Complete FNOL with claim and policy evidence.",
        rationale="All required lookups returned records.",
        tools_used=["fnol_lookup", "claim_lookup", "policy_lookup"],
        confidence=0.9,
    )
    outcome = TriageOutcome(status="completed", decision=decision)
    assert outcome.decision is not None
