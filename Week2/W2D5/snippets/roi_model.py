"""Reference ROI model + local MLflow logging for Day 5 AM Topic 06.

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Verified: MLflow's plain filesystem tracking backend
("./mlruns") is now in maintenance mode as of MLflow 3.14 (July 2026) --
use a sqlite:// tracking URI instead, or the run will fail outright. This
script uses the current, correct pattern.

Run it:
    uv run python W2D5/snippets/roi_model.py
Then view results:
    uv run mlflow ui --backend-store-uri sqlite:///W2D5/outputs/mlflow.db
"""

from __future__ import annotations

from pathlib import Path

import mlflow


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


DB_PATH = discover_repo_root() / "W2D5" / "outputs" / "mlflow.db"


def roi_for_task(cost_usd: float, agent_minutes: float, human_baseline_minutes: float, hourly_rate_usd: float) -> dict:
    """Separates assumptions (rate), quality (unmeasured here -- see Topic 03's eval),
    adoption (not modeled -- assume 100%), gross value, cost, and net value."""
    minutes_saved = human_baseline_minutes - agent_minutes
    gross_value_usd = (minutes_saved / 60) * hourly_rate_usd
    net_value_usd = gross_value_usd - cost_usd
    return {
        "cost_usd": cost_usd,
        "minutes_saved": minutes_saved,
        "gross_value_usd": round(gross_value_usd, 2),
        "net_value_usd": round(net_value_usd, 2),
    }


if __name__ == "__main__":
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{DB_PATH.as_posix()}")
    mlflow.set_experiment("insurance-triage-roi")

    # Real cost figure style from Day 1's /cost readings; substitute your own.
    cases = [
        {"claim_id": "CLM-424063", "cost_usd": 0.014, "agent_minutes": 2.5, "human_baseline_minutes": 12.0},
        {"claim_id": "CLM-748422", "cost_usd": 0.011, "agent_minutes": 2.1, "human_baseline_minutes": 12.0},
        {"claim_id": "CLM-255335", "cost_usd": 0.022, "agent_minutes": 4.0, "human_baseline_minutes": 20.0},
    ]
    hourly_rate_usd = 35.0

    for case in cases:
        result = roi_for_task(case["cost_usd"], case["agent_minutes"], case["human_baseline_minutes"], hourly_rate_usd)
        with mlflow.start_run(run_name=case["claim_id"]):
            mlflow.log_param("claim_id", case["claim_id"])
            mlflow.log_param("hourly_rate_usd", hourly_rate_usd)
            for key, value in result.items():
                mlflow.log_metric(key, value)
        print(case["claim_id"], result)
