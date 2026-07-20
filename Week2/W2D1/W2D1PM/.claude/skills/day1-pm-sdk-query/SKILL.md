---
name: day1-pm-sdk-query
description: Teach one-shot Claude Agent SDK style query() behavior using project CLAUDE.md and insurance fixtures.
disable-model-invocation: true
---

# Day 1 PM — query() style demo

1. Confirm `CLAUDE.md` and `AGENTS.md` exist in `W2D1PM/`.
2. Read FNOL `CLN-001` from fixtures (do not invent).
3. Answer in two short operator sentences: why an agent must use domain tools instead of inventing claim facts.
4. Emit a teaching `ResultMessage`-shaped summary JSON with:
   - `result` (text)
   - `session_id` (any demo uuid)
   - `num_turns`
   - `total_cost_usd` as `"subscription_metered_via_claude_code"`
   - `stop_reason: completed`
5. Remind learners this plugin path uses Claude Code login, not `ANTHROPIC_API_KEY`.
