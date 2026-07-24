"""Phase 6 reference: a pytest suite covering data sanity, guardrail and
agent quality floors, and audit-chain tamper-evidence -- the same "quality
gate that tells you which earlier stage to re-run" pattern as the old
W2D0 capstone's test_capstone.py, applied to this one's phases instead.

Run it:
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" -m pytest W2D0/capstone_ref/test_capstone.py -v
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "outputs"

MIN_AGENT_EVAL_SCORE = 0.90
MIN_INJECTION_SCORE = 0.80
EXPECTED_APPLICANT_ROWS = 491
EXPECTED_LIVE_CASES = 12
EXPECTED_POLICY_FILES = 4


def test_loans_db_seeded_with_expected_shape():
    db_path = DATA_DIR / "loans.db"
    assert db_path.is_file(), "loans.db missing -- run data/seed_loans_db.py (Phase 1) first"
    conn = sqlite3.connect(db_path)
    try:
        (n_applicants,) = conn.execute("SELECT COUNT(*) FROM applicants").fetchone()
        (n_live,) = conn.execute("SELECT COUNT(*) FROM loans WHERE stage IS NOT NULL").fetchone()
    finally:
        conn.close()
    assert n_applicants == EXPECTED_APPLICANT_ROWS, f"expected {EXPECTED_APPLICANT_ROWS} applicants, got {n_applicants}"
    assert n_live == EXPECTED_LIVE_CASES, f"expected {EXPECTED_LIVE_CASES} live cases, got {n_live}"


def test_gold_loan_has_no_policy_document():
    policy_dir = DATA_DIR / "policies"
    files = sorted(p.name for p in policy_dir.glob("*.md"))
    assert len(files) == EXPECTED_POLICY_FILES, f"expected {EXPECTED_POLICY_FILES} policy docs, got {len(files)}: {files}"
    assert not any("GOLD" in f.upper() for f in files), "gold_loan must have NO policy doc -- that's the deliberate gap"


def test_agent_eval_meets_quality_floor():
    replies_path = OUT_DIR / "draft_replies.json"
    assert replies_path.is_file(), (
        "outputs/draft_replies.json missing -- run agent_loop.py (Phase 2) first"
    )
    from eval_gate import run_eval

    outcomes = run_eval()
    score = sum(o["passed"] for o in outcomes) / len(outcomes)
    assert score >= MIN_AGENT_EVAL_SCORE, f"agent eval score {score:.2f} below floor {MIN_AGENT_EVAL_SCORE}"


def test_gold_loan_cases_never_fabricate_a_citation():
    """Independent of the overall floor: this specific guarantee must always hold."""
    import json

    replies = json.loads((OUT_DIR / "draft_replies.json").read_text(encoding="utf-8"))
    gold_replies = [r for r in replies if r.get("product") == "gold_loan"]
    assert len(gold_replies) == 3, f"expected 3 gold_loan replies, found {len(gold_replies)}"
    for r in gold_replies:
        assert not r.get("cited_sources"), f"{r['email_id']} fabricated a citation for an ungrounded product"


def test_injection_scanner_meets_quality_floor():
    from guardrails import run_injection_eval

    outcomes = run_injection_eval()
    score = sum(o["correct"] for o in outcomes) / len(outcomes)
    assert score >= MIN_INJECTION_SCORE, f"injection scanner score {score:.2f} below floor {MIN_INJECTION_SCORE}"


def test_audit_chain_detects_tampering():
    from governance import AuditChain

    chain = AuditChain()
    chain.append({"action": "approved", "email_id": "LN-004", "approver": "jane"})
    chain.append({"action": "rejected", "email_id": "LN-012", "approver": "jane"})
    assert chain.verify() is True

    chain.entries[0]["event"]["approver"] = "attacker"
    assert chain.verify() is False, "tampering with a past entry must be detected"


def test_fraud_case_is_never_auto_approved():
    """The fraud-review case must always land as rejected (routed to a human
    fraud team), never silently approved for auto-send."""
    from governance import ApprovalQueue

    queue_path = OUT_DIR / "approval_queue.db"
    assert queue_path.is_file(), "approval_queue.db missing -- run governance.py (Phase 5) first"
    rows = {row["email_id"]: row for row in ApprovalQueue(queue_path).all()}
    assert "LN-012" in rows, "LN-012 (the fraud-review case) should be in the approval queue"
    assert rows["LN-012"]["status"] == "rejected", "the fraud-review case must not be auto-approved"
