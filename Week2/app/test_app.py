"""Automated test suite for the progressive app, grown one day at a time --
same discipline as W2D4's eval-gate and W2D0's test_capstone.py.

Run it (after app/outputs/lancedb_policies has been built at least once via
`uv run python -m app.rag_index`, or let day3_resolve build it lazily):
    uv run pytest app/test_app.py -v
"""

from __future__ import annotations

import json

import pytest

from app.day1_resolve import resolve_email as day1_resolve_email
from app.day3_resolve import resolve_email as day3_resolve_email
from app.injection_scanner import run_eval as run_injection_eval
from app.trajectory_eval import run_eval as run_trajectory_eval
from app.paths import FNOL_EMAILS_CSV, GOVERNANCE_TIERS
from app.autonomy_check import check_use_case, claims_triage_use_case
from app.audit_chain import AuditChain

# Day 4's quality floors, same thresholds as W2D4/snippets/test_eval_gate.py.
MIN_INJECTION_SCORE = 0.80
MIN_TRAJECTORY_SCORE = 0.90


# --- Day 1: the seed pipeline must ground correctly and escalate on the
# deliberate commercial_package gap, never fabricate coverage for it. ---

def test_day1_grounds_a_known_claim():
    result = day1_resolve_email("CLN-001")
    assert result["found"] is True
    assert result["escalate"] is False
    assert result["claim"]["grounding_available"] is True
    assert "POL-HOME-010" in result["draft_reply"]


def test_day1_escalates_the_deliberate_grounding_gap():
    result = day1_resolve_email("CLN-003")
    assert result["claim"]["product"] == "commercial_package"
    assert result["escalate"] is True
    assert result["draft_reply"] is None


def test_day1_escalates_emails_with_no_claim_number():
    result = day1_resolve_email("CLN-007")
    assert result["found"] is False
    assert result["escalate"] is True


# --- Day 3: coverage answers must be grounded in the CLAIM'S OWN product
# docs, never a different product's policy (the semantic-cache namespace
# bug this app fixed during authoring -- see semantic_cache.py). ---

def test_day3_coverage_excerpt_matches_the_claims_own_product():
    homeowners = day3_resolve_email("CLN-001")
    commercial = day3_resolve_email("CLN-002")
    assert homeowners["coverage_excerpt"] is not None
    assert commercial["coverage_excerpt"] is not None
    assert homeowners["coverage_excerpt"] != commercial["coverage_excerpt"]


def test_day3_fraud_signal_surfaces_the_known_same_address_match():
    result = day3_resolve_email("CLN-001")
    assert result["fraud_signal"]["flag"] is True
    assert "CLM-100234" in result["fraud_signal"]["same_address_claim_ids"]


# --- Day 4: guardrail quality floors, same bar as the original W2D4 gate. ---

def test_injection_scanner_meets_quality_floor():
    outcomes = run_injection_eval()
    score = sum(o["correct"] for o in outcomes) / len(outcomes)
    assert score >= MIN_INJECTION_SCORE, f"injection scanner score {score:.2f} below floor {MIN_INJECTION_SCORE}"


def test_trajectory_eval_meets_quality_floor():
    outcomes = run_trajectory_eval()
    score = sum(o["passed"] for o in outcomes) / len(outcomes)
    assert score >= MIN_TRAJECTORY_SCORE, f"trajectory score {score:.2f} below floor {MIN_TRAJECTORY_SCORE}"


# --- Day 5: governance gate + tamper-evident audit chain. ---

def test_claims_triage_autonomy_is_within_its_risk_tier():
    use_case = claims_triage_use_case()
    check = check_use_case(use_case)
    assert check["within_bounds"] is True
    assert use_case["tier"] == "high"
    assert use_case["autonomy"] == "recommend"


def test_audit_chain_detects_tampering():
    chain = AuditChain()
    chain.append({"action": "test_event", "claim_id": "CLM-000000"})
    assert chain.verify() is True
    chain.entries[0]["event"]["claim_id"] = "TAMPERED"
    assert chain.verify() is False


def test_governance_fixture_has_the_claims_triage_entry():
    data = json.loads(GOVERNANCE_TIERS.read_text(encoding="utf-8"))
    ids = [uc["id"] for uc in data["use_cases"]]
    assert "claims-triage" in ids


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
