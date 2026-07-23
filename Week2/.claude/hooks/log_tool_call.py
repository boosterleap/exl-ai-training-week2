#!/usr/bin/env python
"""PreToolUse hook: append a one-line JSON log entry for every tool call."""
import datetime
import json
import pathlib
import sys


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "tool_name": data.get("tool_name"),
        "arguments": data.get("tool_input"),
    }

    project_root = pathlib.Path(__file__).resolve().parents[2]
    out_dir = project_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "tool_call_log.jsonl"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
