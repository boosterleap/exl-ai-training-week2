"""Reference autonomy-matrix check for Day 5 PM Topic 02.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Reads data/governance/use_case_risk_tiers.json and
checks: does declared autonomy level make sense for the declared risk
tier? Verified: "claims-triage" (high tier) declares "recommend" autonomy
(not "act") -- correctly conservative given the tier's required_controls
list (approval, audit, explainability, appeal, monitoring).

Run it:
    uv run python W2D5/snippets/autonomy_matrix.py
"""

from __future__ import annotations

import json
from pathlib import Path

# Autonomy levels, most to least autonomous. A high-risk use case should
# never sit above "recommend" without every one of its tier's required
# controls in place.
AUTONOMY_RANK = {"act": 3, "approve": 2, "review": 2, "recommend": 1, "human_decides": 0, "assist": 0}
MAX_AUTONOMY_BY_TIER = {"low": 3, "medium": 2, "high": 1}


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


TIERS_PATH = discover_repo_root() / "data" / "governance" / "use_case_risk_tiers.json"


def check_use_case(use_case: dict) -> dict:
    tier = use_case["tier"]
    autonomy_rank = AUTONOMY_RANK[use_case["autonomy"]]
    max_allowed = MAX_AUTONOMY_BY_TIER[tier]
    return {
        "id": use_case["id"],
        "tier": tier,
        "autonomy": use_case["autonomy"],
        "within_bounds": autonomy_rank <= max_allowed,
    }


if __name__ == "__main__":
    data = json.loads(TIERS_PATH.read_text(encoding="utf-8"))
    for use_case in data["use_cases"]:
        result = check_use_case(use_case)
        marker = "OK  " if result["within_bounds"] else "FLAG"
        print(f"{marker} {result['id']:20s} tier={result['tier']:7s} autonomy={result['autonomy']}")
