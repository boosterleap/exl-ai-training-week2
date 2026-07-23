#!/bin/bash
# Token Summary Hook
# Displays session token usage after each tool batch
# Reads from Claude Code's session data

USAGE_LOG="outputs/token_summary.log"
mkdir -p outputs

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SESSION TOKEN USAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get the latest session file
SESSION_FILE=$(ls -t ~/.claude/sessions/*.json 2>/dev/null | head -1)

if [ -f "$SESSION_FILE" ]; then
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
  SESSION_ID=$(jq -r '.sessionId' "$SESSION_FILE" 2>/dev/null)
  TURN_NUM=$(jq -r '.turnNumber // 0' "$SESSION_FILE" 2>/dev/null)

  echo "  Session ID: $SESSION_ID"
  echo "  Turn: $TURN_NUM"
  echo "  Timestamp: $TIMESTAMP"

  # Log to file for historical tracking
  echo "$TIMESTAMP | Session: $SESSION_ID | Turn: $TURN_NUM" >> "$USAGE_LOG"
else
  echo "  (Session data not found)"
fi

# Try to extract token info from tool_call_log.jsonl
TOOL_LOG="outputs/tool_call_log.jsonl"

if [ -f "$TOOL_LOG" ]; then
  echo ""
  echo "  Recent Tool Calls:"

  C:\users\asus\.venv\Scripts\python.exe << 'PYEOF'
import json
import sys

try:
    with open('outputs/tool_call_log.jsonl', 'r') as f:
        lines = f.readlines()

    if not lines:
        print("    (no tool calls yet)")
        sys.exit(0)

    # Parse last 10 entries
    recent = lines[-10:]

    total_input = 0
    total_output = 0
    call_count = 0

    for line in recent:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            tool = entry.get('tool') or entry.get('tool_name', '?')
            inp = entry.get('input_tokens') or 0
            out = entry.get('output_tokens') or 0

            if inp or out:
                total_input += inp
                total_output += out
                call_count += 1
                print(f"    {tool:20s} → in: {inp:6d}, out: {out:6d}")
        except:
            pass

    if call_count > 0:
        print(f"    {'-'*50}")
        print(f"    {'TOTAL':20s} → in: {total_input:6d}, out: {total_output:6d} (total: {total_input + total_output})")
    else:
        print("    (tokens not tracked in this session yet)")
except Exception as e:
    print(f"    (could not parse tool log: {e})")

PYEOF
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
