#!/usr/bin/env python
"""PostToolUse hook for mcp__insurance-lookup__get_claim_and_policy.

Appends a log entry for the tool's response to outputs/tool_call_log.jsonl
with named_insured redacted. This only affects the logged copy -- PostToolUse
hooks run after the real result has already been returned to Claude, so the
answer-generation path is untouched.
"""
import datetime
import json
import pathlib
import sys

REDACTED = "[REDACTED]"


def redact(value):
    if isinstance(value, dict):
        redacted = {}
        for key, val in value.items():
            if key == "named_insured":
                redacted[key] = REDACTED
            elif isinstance(val, str):
                redacted[key] = _redact_if_json_string(val)
            else:
                redacted[key] = redact(val)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def _redact_if_json_string(text):
    stripped = text.strip()
    if not stripped or stripped[0] not in "{[":
        return text
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return json.dumps(redact(parsed))


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}

    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": "PostToolUse",
        "tool_name": data.get("tool_name"),
        "arguments": data.get("tool_input"),
        "response": redact(data.get("tool_response")),
    }

    project_root = pathlib.Path(__file__).resolve().parents[2]
    out_dir = project_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "tool_call_log.jsonl"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
