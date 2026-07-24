"""Phase 5 reference: score agent_loop.py's draft replies against a golden
set derived from inbound_emails.csv's own ground-truth columns, and gate on
a quality floor rather than demanding a perfect score.

Two things are graded per email:
  - escalation correctness: escalated must be True iff the product is
    gold_loan (the deliberate grounding gap)
  - citation correctness: for a documented product, cited_sources must
    include that product's own policy file; for gold_loan, it must be empty

Run it:
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/eval_gate.py
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" -m pytest W2D0/capstone_ref/eval_gate.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tools import PRODUCT_TO_POLICY_PREFIX

DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "outputs"

MIN_SCORE = 0.90  # quality floor -- ship at or above this, not "must be perfect"


def build_goldens() -> dict[str, dict]:
    emails = pd.read_csv(DATA_DIR / "inbound_emails.csv")
    goldens = {}
    for _, row in emails.iterrows():
        product = row["product_ground_truth"]
        prefix = PRODUCT_TO_POLICY_PREFIX.get(product)
        goldens[row["email_id"]] = {
            "loan_id": row["loan_id_ground_truth"],
            "product": product,
            "expected_escalated": prefix is None,
            "expected_citation_prefix": prefix,
        }
    return goldens


def score_reply(golden: dict, reply: dict) -> dict:
    escalation_correct = bool(reply.get("escalated")) == golden["expected_escalated"]
    cited = reply.get("cited_sources") or []
    if golden["expected_citation_prefix"] is None:
        citation_correct = len(cited) == 0
    else:
        citation_correct = any(c.startswith(golden["expected_citation_prefix"]) for c in cited)
    return {
        "escalation_correct": escalation_correct,
        "citation_correct": citation_correct,
        "passed": escalation_correct and citation_correct,
    }


def run_eval() -> list[dict]:
    goldens = build_goldens()
    replies = json.loads((OUT_DIR / "draft_replies.json").read_text(encoding="utf-8"))
    outcomes = []
    for reply in replies:
        golden = goldens[reply["email_id"]]
        scored = score_reply(golden, reply)
        scored["id"] = reply["email_id"]
        outcomes.append(scored)
    return outcomes


def test_agent_meets_quality_floor():
    outcomes = run_eval()
    score = sum(o["passed"] for o in outcomes) / len(outcomes)
    assert score >= MIN_SCORE, f"agent eval score {score:.2f} below floor {MIN_SCORE}"


if __name__ == "__main__":
    outcomes = run_eval()
    for o in outcomes:
        marker = "PASS" if o["passed"] else "FAIL"
        print(f"{marker} {o['id']:8s} escalation={o['escalation_correct']} citation={o['citation_correct']}")
    score = sum(o["passed"] for o in outcomes) / len(outcomes)
    print(f"\n{sum(o['passed'] for o in outcomes)}/{len(outcomes)} passed ({score:.2f}), floor is {MIN_SCORE}")
