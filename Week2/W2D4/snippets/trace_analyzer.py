"""Reference local trace analyzer for Day 4 PM Topic 01 (observability).

Fallback/reference only -- the session guide asks you to have Claude Code
build this with you. Reads a JSONL tool-call trace (the same shape Day 2
AM's PreToolUse hook writes to outputs/tool_call_log.jsonl) and surfaces:
per-tool call counts, total/average latency, and a simple repeated-call
anomaly detector -- the same tool called with the same arguments 3+ times
is exactly the loop-detection signal from Day 1 Topic 06, now applied to
a real trace instead of described in the abstract.

Verified against snippets/sample_trace.jsonl: correctly flags
mcp__insurance-lookup__get_claim_and_policy(claim_id=CLM-999999) as
called 3 times with rising latency (411/388/402ms vs ~40ms for a normal
lookup) -- a strong "this claim doesn't exist, stop retrying" signal.

Run it:
    uv run python W2D4/snippets/trace_analyzer.py
    # or point it at your own real trace:
    uv run python W2D4/snippets/trace_analyzer.py outputs/tool_call_log.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPEAT_THRESHOLD = 3


def load_trace(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _tool_name(event: dict) -> str:
    # PreToolUse-only hooks (log_tool_call.py) write "tool_name", not "tool" --
    # the sample_trace.jsonl fixture uses "tool". Accept either.
    return event.get("tool") or event.get("tool_name")


def analyze(events: list[dict]) -> dict:
    tool_counts = Counter(_tool_name(e) for e in events)
    latencies = defaultdict(list)
    for e in events:
        if "duration_ms" in e:
            latencies[_tool_name(e)].append(e["duration_ms"])

    call_signatures = Counter((_tool_name(e), json.dumps(e.get("arguments", {}), sort_keys=True)) for e in events)
    repeated = [
        {"tool": tool, "arguments": json.loads(args_json), "count": count}
        for (tool, args_json), count in call_signatures.items()
        if count >= REPEAT_THRESHOLD
    ]

    return {
        "total_calls": len(events),
        "calls_by_tool": dict(tool_counts),
        # Only tools with at least one timed call get an average; a PreToolUse-only
        # hook never records duration_ms, so most real traces will have none here --
        # that's reported honestly below, not defaulted to 0ms.
        "avg_latency_ms_by_tool": {tool: round(sum(ms) / len(ms), 1) for tool, ms in latencies.items() if ms},
        "repeated_identical_calls": repeated,
    }


if __name__ == "__main__":
    default_path = Path(__file__).resolve().parent / "sample_trace.jsonl"
    trace_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_path
    report = analyze(load_trace(trace_path))

    print(f"Trace: {trace_path}")
    print(f"Total calls: {report['total_calls']}")
    print("\nCalls by tool:")
    for tool, count in report["calls_by_tool"].items():
        avg = report["avg_latency_ms_by_tool"].get(tool)
        latency_note = f"avg {avg}ms" if avg is not None else "no duration_ms in trace"
        print(f"  {count:3d}  {tool}  ({latency_note})")
    if report["repeated_identical_calls"]:
        print("\nANOMALY: repeated identical calls (possible stuck loop):")
        for r in report["repeated_identical_calls"]:
            print(f"  {r['tool']} called {r['count']}x with {r['arguments']}")
    else:
        print("\nNo repeated-call anomalies detected.")
