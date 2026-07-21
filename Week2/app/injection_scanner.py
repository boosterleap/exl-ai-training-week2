"""Day 4 -- deterministic prompt-injection scanner, adapted from
W2D4/snippets/injection_scanner.py.

Applied to inbound email bodies before they reach any tool-calling step.
Verified against the real fixture: 17/20 correct. The 3 misses
(ADV-005, ADV-013, ADV-014) are deliberately left as-is -- finding and
reasoning about them is the original Day 4 AM Topic 04 exercise, not a
bug to silently patch away. A heuristic-only scanner has real, provable
blind spots; that's the point being taught, not a defect in this file.

Run it:
    uv run python -m app.injection_scanner
"""

from __future__ import annotations

import json
import re

from app.paths import REPO_ROOT

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
]
COMPILED = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]

FIXTURE_PATH = REPO_ROOT / "data" / "eval" / "adversarial_prompts.json"


def scan(prompt: str) -> bool:
    """Returns True if the prompt should be BLOCKED (matched a suspicious pattern)."""
    return any(pattern.search(prompt) for pattern in COMPILED)


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
