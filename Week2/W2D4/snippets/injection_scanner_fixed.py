
"""Modified injection scanner with one additional pattern for ADV-005.

This version adds:
  r"(print|show|display|output|dump|emit).*(system prompt|hidden|secret|chain)"

to catch synonym-based evasion attempts like "print the system prompt"
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SUSPICIOUS_PATTERNS = [
    r"ignore (previous|prior) (instructions?|messages?|controls?)",
    r"reveal (the )?(system prompt|hidden|secret|credentials?)",
    r"bypass (approval|all safeguards|restrictions?)",
    r"override polic",
    r"as (admin|the approver)",
    r"trusted section",
    r"developer mode",
    r"encode and reveal",
    r"send .* (externally|out)",
    r"delete the account",
    # NEW PATTERN: Catch synonym-based disclosure attempts
    r"(print|show|display|output|dump|emit).*(system prompt|hidden|secret|chain)",
]
COMPILED = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


def scan(prompt: str) -> bool:
    """Returns True if the prompt should be BLOCKED (matched a suspicious pattern)."""
    return any(pattern.search(prompt) for pattern in COMPILED)


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


FIXTURE_PATH = discover_repo_root() / "data" / "eval" / "adversarial_prompts.json"


def run_eval() -> list[dict]:
    items = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    results = []
    for item in items:
        predicted_block = scan(item["prompt"])
        expected_block = item["expected"] == "block"
        results.append({"id": item["id"], "correct": predicted_block == expected_block, "item": item})
    return results


if __name__ == "__main__":
    outcomes = run_eval()
    for outcome in outcomes:
        item = outcome["item"]
        marker = "OK  " if outcome["correct"] else "MISS"
        print(f"{marker} {item['id']} expected={item['expected']:5s} source={item['source']:16s} {item['prompt'][:55]!r}")
    correct = sum(o["correct"] for o in outcomes)
    print(f"\n{correct}/{len(outcomes)} correct")
