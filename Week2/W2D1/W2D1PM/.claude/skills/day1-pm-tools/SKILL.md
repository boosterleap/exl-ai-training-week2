---
name: day1-pm-tools
description: Teach built-in Read vs custom domain tools and grounded triage for CLN-001.
disable-model-invocation: true
---

# Day 1 PM — tools / MCP naming demo

1. Use Read on `W2D1PM/CLAUDE.md` and state the first operator rule.
2. Explain MCP-style names: `mcp__insurance__fnol_lookup`, `mcp__insurance__claim_lookup`, `mcp__insurance__policy_lookup`.
3. Perform grounded triage for `CLN-001` by reading fixtures (CSV + sqlite).
4. Return `TriageDecision` JSON with evidence-backed `case_id` starting `CLM-`.
5. List `called_tools` conceptually as the three insurance tools.
6. Contrast: if allowlist were FNOL-only, claim/policy tools must be absent (Exercise PM-1).
