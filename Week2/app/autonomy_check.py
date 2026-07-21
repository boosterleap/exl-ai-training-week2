"""Day 5 -- autonomy-vs-risk-tier check, adapted from
W2D5/snippets/autonomy_matrix.py.

Reads data/governance/use_case_risk_tiers.json and checks: does the
declared autonomy level make sense for the declared risk tier? This
app's own claims-triage pipeline is gated against the real "claims-triage"
entry (high tier, "recommend" autonomy) in day5_resolve.py.

Run it:
    uv run python -m app.autonomy_check
"""

from __future__ import annotations

import json

from app.paths import GOVERNANCE_TIERS

# Autonomy levels, most to least autonomous. A high-risk use case should
# never sit above "recommend" without every one of its tier's required
# controls in place.
AUTONOMY_RANK = {"act": 3, "approve": 2, "review": 2, "recommend": 1, "human_decides": 0, "assist": 0}
MAX_AUTONOMY_BY_TIER = {"low": 3, "medium": 2, "high": 1}


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


def claims_triage_use_case() -> dict:
    data = json.loads(GOVERNANCE_TIERS.read_text(encoding="utf-8"))
    for use_case in data["use_cases"]:
        if use_case["id"] == "claims-triage":
            return use_case
    raise ValueError("claims-triage use case not found in use_case_risk_tiers.json")


if __name__ == "__main__":
    data = json.loads(GOVERNANCE_TIERS.read_text(encoding="utf-8"))
    for use_case in data["use_cases"]:
        result = check_use_case(use_case)
        marker = "OK  " if result["within_bounds"] else "FLAG"
        print(f"{marker} {result['id']:20s} tier={result['tier']:7s} autonomy={result['autonomy']}")
