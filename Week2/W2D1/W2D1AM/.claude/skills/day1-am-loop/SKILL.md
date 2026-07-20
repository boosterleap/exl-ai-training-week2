---
name: day1-am-loop
description: Run the Day 1 AM agentic-loop teaching demo for FNOL CLN-001 using insurance fixtures only.
disable-model-invocation: true
---

# Day 1 AM — Agentic loop demo

1. Read `Week2/data/insurance/fnol_emails.csv` and locate `CLN-001`.
2. From that row, extract claim and policy identifiers. Do not invent IDs.
3. Look up the claim and policy in `Week2/data/insurance/claims.db` with sqlite if needed.
4. Explain the observe → decide → act → observe loop in 4 short bullets for an operator.
5. Produce a `TriageDecision`-shaped JSON using only fixture evidence.
6. State `stop_reason: completed` and list tools/files you used.
