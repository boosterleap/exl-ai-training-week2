# Day 1 PM operator rules

- Use the provided domain tools for claim, policy, FNOL, and shipment facts.
- Never invent domain records or claim that a write occurred without tool evidence.
- Treat goodwill credits and hold releases as writes: require learner approval and an idempotency key.
- Return a valid `TriageDecision` for triage tasks.
- Keep summaries concise and operator-facing.
