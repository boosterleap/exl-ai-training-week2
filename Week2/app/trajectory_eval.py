"""Day 4 -- trajectory evaluator, adapted from W2D4/snippets/trajectory_eval.py.

Scores the WHOLE path (tool selection, step count, policy compliance), not
just the final answer. Verified against the real fixture: 25/26 pass;
TRJ-026-INTENTIONAL-FAIL is correctly localized.

Run it:
    uv run python -m app.trajectory_eval
"""

from __future__ import annotations

import json

from app.paths import REPO_ROOT

GOLDENS_PATH = REPO_ROOT / "data" / "eval" / "trajectory_goldens.json"


def score_trajectory(row: dict) -> dict:
    tool_selection_correct = row["actual_tools"] == row["expected_tools"]
    within_step_budget = len(row["actual_tools"]) <= row["max_steps"]
    passed = tool_selection_correct and within_step_budget and row["policy_compliant"] and row["task_success"]
    return {
        "id": row["id"],
        "passed": passed,
        "tool_selection_correct": tool_selection_correct,
        "within_step_budget": within_step_budget,
        "policy_compliant": row["policy_compliant"],
        "task_success": row["task_success"],
    }


def run_eval() -> list[dict]:
    rows = json.loads(GOLDENS_PATH.read_text(encoding="utf-8"))
    return [score_trajectory(row) for row in rows]


if __name__ == "__main__":
    outcomes = run_eval()
    for outcome in outcomes:
        marker = "PASS" if outcome["passed"] else "FAIL"
        print(f"{marker} {outcome['id']:28s} tools={outcome['tool_selection_correct']} "
              f"budget={outcome['within_step_budget']} compliant={outcome['policy_compliant']}")
    passed = sum(o["passed"] for o in outcomes)
    print(f"\n{passed}/{len(outcomes)} trajectories pass")
