#!/usr/bin/env python3
"""
Parse Claude Code usage data from session files and logs.
Extracts and displays token usage across sessions.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def get_latest_session():
    """Find the most recent Claude Code session."""
    sessions_dir = Path.home() / ".claude" / "sessions"
    if not sessions_dir.exists():
        return None

    sessions = sorted(
        sessions_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return sessions[0] if sessions else None

def read_session_data(session_file):
    """Read session metadata."""
    try:
        with open(session_file, 'r') as f:
            return json.load(f)
    except:
        return None

def parse_tool_log():
    """Parse tool_call_log.jsonl for token data."""
    tool_log = Path("outputs/tool_call_log.jsonl")
    if not tool_log.exists():
        return []

    data = []
    try:
        with open(tool_log, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        data.append(entry)
                    except:
                        pass
    except:
        pass

    return data

def aggregate_tokens(tool_log_data):
    """Aggregate token counts from tool log."""
    total_input = 0
    total_output = 0
    by_tool = {}

    for entry in tool_log_data:
        tool = entry.get('tool') or entry.get('tool_name', 'unknown')
        inp = entry.get('input_tokens') or 0
        out = entry.get('output_tokens') or 0

        total_input += inp
        total_output += out

        if tool not in by_tool:
            by_tool[tool] = {'input': 0, 'output': 0, 'count': 0}

        by_tool[tool]['input'] += inp
        by_tool[tool]['output'] += out
        by_tool[tool]['count'] += 1

    return {
        'total_input': total_input,
        'total_output': total_output,
        'total': total_input + total_output,
        'by_tool': by_tool
    }

def print_report(session_data, aggregated):
    """Print formatted token usage report."""
    print("\n" + "=" * 70)
    print("CLAUDE CODE TOKEN USAGE REPORT")
    print("=" * 70)

    if session_data:
        session_id = session_data.get('sessionId', 'unknown')[:8]
        started = session_data.get('startedAt')
        if started:
            dt = datetime.fromtimestamp(started / 1000)
            print(f"Session:  {session_id} ({dt.strftime('%Y-%m-%d %H:%M:%S')})")

    print("\nTOKEN SUMMARY:")
    print(f"  Input tokens:       {aggregated['total_input']:>10,}")
    print(f"  Output tokens:      {aggregated['total_output']:>10,}")
    print(f"  Total tokens:       {aggregated['total']:>10,}")

    if aggregated['by_tool']:
        print("\nBREAKDOWN BY TOOL:")
        print(f"  {'Tool':<20} {'Calls':>6} {'Input':>10} {'Output':>10} {'Total':>10}")
        print("  " + "-" * 60)

        for tool in sorted(aggregated['by_tool'].keys()):
            info = aggregated['by_tool'][tool]
            print(f"  {tool:<20} {info['count']:>6} {info['input']:>10,} {info['output']:>10,} {info['input']+info['output']:>10,}")

    print("\n" + "=" * 70)

def main():
    # Get latest session
    session_file = get_latest_session()
    session_data = None

    if session_file:
        session_data = read_session_data(session_file)

    # Parse tool log
    tool_log_data = parse_tool_log()

    if not tool_log_data:
        print("No token data found. Run some queries first.")
        return

    # Aggregate
    aggregated = aggregate_tokens(tool_log_data)

    # Print
    print_report(session_data, aggregated)

if __name__ == "__main__":
    main()
