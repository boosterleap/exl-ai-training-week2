---
name: day1-pm-budget
description: Teach client-side max_budget_usd awareness and ResultMessage metering fields.
disable-model-invocation: true
---

# Day 1 PM — cost awareness

1. Run a short grounded-claims explanation (no invented facts).
2. Emit metering JSON with fields analogous to SDK `ResultMessage`:
   - `max_budget_usd` (use `0.01` for the tiny-budget exercise)
   - `total_cost_usd` note that plugin usage is subscription-metered
   - `num_turns`, `stop_reason`, `subtype`, `usage`
3. Write `Week2/W2D1/outputs/day1/usage_summary_plugin.json` if writes are allowed.
4. Contrast default budget vs tiny `0.01` budget as a teaching story (Exercise PM-2).
