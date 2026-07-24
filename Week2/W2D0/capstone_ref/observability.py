"""Phase 5 reference: analyze the tool-call trace agent_loop.py now writes
to outputs/tool_trace.jsonl -- per-tool call counts, average latency, and a
repeated-identical-call anomaly detector.

Adapts W2D4/snippets/trace_analyzer.py to this capstone's trace shape
(email_id, tool, arguments, duration_ms).

Run it (after running agent_loop.py at least once):
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/observability.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

REPEAT_THRESHOLD = 3
TRACE_PATH = Path(__file__).parent / "outputs" / "tool_trace.jsonl"


def load_trace(path: Path = TRACE_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def analyze(events: list[dict]) -> dict:
    tool_counts = Counter(e["tool"] for e in events)
    latencies = defaultdict(list)
    for e in events:
        latencies[e["tool"]].append(e["duration_ms"])

    call_signatures = Counter((e["tool"], json.dumps(e["arguments"], sort_keys=True)) for e in events)
    repeated = [
        {"tool": tool, "arguments": json.loads(args_json), "count": count}
        for (tool, args_json), count in call_signatures.items()
        if count >= REPEAT_THRESHOLD
    ]

    return {
        "total_calls": len(events),
        "calls_by_tool": dict(tool_counts),
        "avg_latency_ms_by_tool": {tool: round(sum(ms) / len(ms), 1) for tool, ms in latencies.items()},
        "repeated_identical_calls": repeated,
        "distinct_emails_traced": len({e["email_id"] for e in events}),
    }


if __name__ == "__main__":
    report = analyze(load_trace())
    print(f"Trace: {TRACE_PATH}")
    print(f"Total tool calls: {report['total_calls']} across {report['distinct_emails_traced']} emails")
    print("\nCalls by tool:")
    for tool, count in report["calls_by_tool"].items():
        avg = report["avg_latency_ms_by_tool"][tool]
        print(f"  {count:3d}  {tool:20s} avg {avg}ms")
    if report["repeated_identical_calls"]:
        print("\nANOMALY: repeated identical calls (possible stuck loop):")
        for r in report["repeated_identical_calls"]:
            print(f"  {r['tool']} called {r['count']}x with {r['arguments']}")
    else:
        print("\nNo repeated-call anomalies detected.")
