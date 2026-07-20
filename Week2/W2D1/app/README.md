# Day 1 application structure (study only)

Learners do **not** execute this package. It shows how the Week 2 Agentic Operations Assistant is organized after Day 1.

Later days grow this same day-level `app/` layout (no AM/PM split). Day 1 establishes the core loop, tools, grounding, sessions, permissions, and cost bounds.

## Folder map

```text
W2D1/app/
  README.md                 this guide
  main.py                   thin CLI entry points for study
  config.py                 paths, model name, simple budgets
  models/
    triage.py               TriageDecision and related contracts
  tools/
    insurance.py            FNOL / claim / policy reads
    logistics.py            shipment lookup and hold-release write
  agents/
    langgraph_triage.py     LangGraph model + ToolNode loop
    sdk_assistant.py        Claude Agent SDK query / client shape
  memory/
    checkpoints.py          checkpoint / session id helpers
  permissions/
    gates.py                allowed tools, approval, idempotency
  grounding/
    validate.py             evidence checks for TriageDecision
  artifacts/
    handoff.py              Day 2 handoff preview shape
```

## Application flow

```text
operator request
   → main.py selects lane command (triage | release)
   → config.py loads Week2 paths and model settings
   → tools/* return authoritative records only
   → agents/langgraph_triage.py or agents/sdk_assistant.py
        run the observe → decide → act → observe loop
   → grounding/validate.py accepts or rejects the decision
   → permissions/gates.py blocks writes without approval
   → memory/checkpoints.py records session / thread ids
   → artifacts/handoff.py shapes the Day 2 handoff preview
```

## What each package owns

| Package | Responsibility |
| --- | --- |
| `models` | Stable Pydantic contracts shared by both agent paths |
| `tools` | Domain reads and the one permission-gated write |
| `agents` | LangGraph and Claude Agent SDK orchestration |
| `memory` | Working session / checkpoint identifiers |
| `permissions` | `allowed_tools`, approval, and idempotency |
| `grounding` | Evidence-backed validation of structured decisions |
| `artifacts` | Versioned handoff object for later days |

## Study path

1. Read `config.py` and `models/triage.py`.
2. Read `tools/insurance.py` and `tools/logistics.py`.
3. Compare `agents/langgraph_triage.py` with `agents/sdk_assistant.py`.
4. Read `grounding/validate.py`, then `permissions/gates.py`.
5. Finish with `memory/checkpoints.py` and `artifacts/handoff.py`.
6. Open `main.py` last to see how the pieces are wired.

Executable teaching content lives in the Day 1 demonstration notebooks and the Agentic-libraries primers, not in this package.

## Optional smoke check

If you want to confirm imports resolve, from `W2D1/app`:

```powershell
uv run main.py
```

Or from `W2D1`:

```powershell
uv run python -m app.main
```

This only exercises the study wiring helpers. It is not the Day 1 lab path.
