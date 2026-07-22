"""Reference trajectory evaluator for Day 4 PM Topic 02.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Scores the WHOLE path (tool selection, step count,
policy compliance), not just the final answer. Verified against the real
fixture: 25/26 pass; TRJ-026-INTENTIONAL-FAIL is correctly localized --
its actual_tools skipped straight to release_hold without the expected
check_permission/request_approval steps first.

Run it:
    uv run python W2D4/snippets/trajectory_eval.py
"""

from __future__ import annotations

import json
from pathlib import Path


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


GOLDENS_PATH = discover_repo_root() / "data" / "eval" / "trajectory_goldens.json"


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
