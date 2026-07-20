---
name: day1-am-grounding
description: Compare grounded triage for CLN-001 vs fail-closed CLN-007 using insurance fixtures.
disable-model-invocation: true
---

# Day 1 AM — Grounding / fail-closed demo

1. Read FNOL for `CLN-001` and for `CLN-007` from `fnol_emails.csv`.
2. For each email_id, attempt a grounded `TriageDecision`.
3. Rules:
   - `case_id` must be a real claim id from evidence (`CLM-######`).
   - If FNOL has no claim number / incomplete evidence, return `status: refused` with `refusal_reason`.
4. Display a side-by-side JSON: `{ "CLN-001": ..., "CLN-007": ... }`.
5. Never invent a claim id for CLN-007.
