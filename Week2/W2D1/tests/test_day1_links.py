"""Verify Day 1 study and demo entry points exist after the restructure."""

from __future__ import annotations

from pathlib import Path

DAY_DIR = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    DAY_DIR / "app" / "README.md",
    DAY_DIR / "app" / "main.py",
    DAY_DIR / "app" / "models" / "triage.py",
    DAY_DIR / "W2D1AM" / "_DEMONSTRATIONS.ipynb",
    DAY_DIR / "W2D1PM" / "_DEMONSTRATIONS.ipynb",
    DAY_DIR / "W2D1PM" / "_ARCHITECTURE_COMPARISON.ipynb",
    DAY_DIR / "W2D1PM" / "CLAUDE.md",
    DAY_DIR / "W2D1PM" / "AGENTS.md",
    DAY_DIR / "Agentic-libraries" / "01_LANGGRAPH_PRIMER.ipynb",
    DAY_DIR / "Agentic-libraries" / "02_CLAUDE_AGENT_SDK_PRIMER.ipynb",
]


def test_day1_study_and_demo_paths_exist() -> None:
    missing = [str(path.relative_to(DAY_DIR)) for path in REQUIRED_PATHS if not path.exists()]
    assert not missing, "Missing Day 1 paths:\n" + "\n".join(missing)
