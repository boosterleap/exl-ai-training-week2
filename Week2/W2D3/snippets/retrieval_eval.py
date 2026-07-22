"""Reference retrieval eval for Day 3 PM Topic 02 (KB engineering).

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Runs data/insurance/rag_goldens.json against Day 3
AM's rag_index.search(), checking whether at least one retrieved chunk
comes from an expected policy document (policy-level precision@k -- the
goldens' required_chunk_ids use a slugified id scheme rag_index.py does
not generate, so this checks the coarser, still-meaningful policy level).

Verified result on the real fixture: 4/5 pass. G-003 fails not because
retrieval is wrong, but because the golden's expected_policy_ids says
"POL-HOME-FLOOD" while the actual file is POL-HOME-010_flood_rider.md --
a mismatch in the golden fixture itself. Finding and diagnosing that is
the point of Day 3 PM's Topic 02 exercise, not just running the eval.

Run it:
    uv run python W2D3/snippets/retrieval_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def discover_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "_DATA_README.md").is_file():
            return parent
    raise RuntimeError("Could not discover the Week 2 (Claude Code) repo root.")


REPO_ROOT = discover_repo_root()
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rag_index import build_index, search  # noqa: E402

GOLDENS_PATH = REPO_ROOT / "data" / "insurance" / "rag_goldens.json"


def run_eval(k: int = 3) -> list[dict]:
    goldens = json.loads(GOLDENS_PATH.read_text(encoding="utf-8"))["goldens"]
    results = []
    for golden in goldens:
        hits = search(golden["question"], k=k)
        expected = tuple(golden["expected_policy_ids"])
        passed = any(hit["source_file"].startswith(expected) for hit in hits)
        results.append(
            {
                "question_id": golden["question_id"],
                "question": golden["question"],
                "passed": passed,
                "top_hit": hits[0]["source_file"] if hits else None,
            }
        )
    return results


if __name__ == "__main__":
    build_index()
    outcomes = run_eval()
    for outcome in outcomes:
        status = "PASS" if outcome["passed"] else "FAIL"
        print(f"{outcome['question_id']} {status} - {outcome['question'][:55]!r} (top: {outcome['top_hit']})")
    passed_count = sum(o["passed"] for o in outcomes)
    print(f"\n{passed_count}/{len(outcomes)} policy-level precision@3")
