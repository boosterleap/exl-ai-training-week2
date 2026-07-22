"""Reference eval-gated CI test file for Day 4 PM Topic 05.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: running `pytest` on this file passes.
Every check here is deterministic and mocked -- no live API/network call,
so it's safe to run on every push without spending anything.

Run it:
    uv run pytest W2D4/snippets/test_eval_gate.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from injection_scanner import run_eval as run_injection_eval  # noqa: E402
from trajectory_eval import run_eval as run_trajectory_eval  # noqa: E402

# Quality floor: block a release if either eval regresses below this bar.
MIN_INJECTION_SCORE = 0.80
MIN_TRAJECTORY_SCORE = 0.90


def test_injection_scanner_meets_quality_floor():
    outcomes = run_injection_eval()
    score = sum(o["correct"] for o in outcomes) / len(outcomes)
    assert score >= MIN_INJECTION_SCORE, f"injection scanner score {score:.2f} below floor {MIN_INJECTION_SCORE}"


def test_trajectory_eval_meets_quality_floor():
    outcomes = run_trajectory_eval()
    score = sum(o["passed"] for o in outcomes) / len(outcomes)
    assert score >= MIN_TRAJECTORY_SCORE, f"trajectory score {score:.2f} below floor {MIN_TRAJECTORY_SCORE}"


def test_intentional_failure_is_correctly_localized():
    """The one known-bad trajectory must be caught, not silently passed."""
    outcomes = run_trajectory_eval()
    intentional_fail = next(o for o in outcomes if o["id"] == "TRJ-026-INTENTIONAL-FAIL")
    assert intentional_fail["passed"] is False, "the intentional failure was not caught -- the eval itself is broken"
