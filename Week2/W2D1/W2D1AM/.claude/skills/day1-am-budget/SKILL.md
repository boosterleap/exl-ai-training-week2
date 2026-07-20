---
name: day1-am-budget
description: Teach application-owned model-call budgets by simulating budget=1 vs budget=3 for CLN-001.
disable-model-invocation: true
---

# Day 1 AM — Budget / stop_reason demo

Simulate an application-owned loop that must call fnol → claim → policy for CLN-001.

1. With `max_model_calls=1`: show that the loop stops with `stop_reason: model_call_budget_exhausted` before all tools can finish.
2. With `max_model_calls=3`: show a different stop profile (`completed` or continued tool progress) and higher `model_calls`.
3. Return JSON:
   `{ "budget_1": {...}, "budget_3": {...} }`
4. Teach: the application owns stop conditions; the model does not.
