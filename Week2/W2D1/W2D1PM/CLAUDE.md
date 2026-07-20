# Agentic Operations Assistant context

This project supports three business lanes:

- insurance: FNOL triage using policy and claim tools
- banking: loan servicing with resumable customer sessions
- logistics: shipment status and permission-gated hold releases

Rules:

- Use domain tools for factual data.
- Never invent claim, loan, policy, or shipment records.
- Treat goodwill credits and hold releases as write operations.
- Write operations require learner approval and an idempotency key.
- Return a valid `TriageDecision` object.
- Keep summaries concise and operator-facing.
