# The progressive insurance app (reference / fallback)

Reference/fallback only, same as the `W2Dx/snippets/` files it mirrors — the
session guides ask you to have Claude Code build the real thing with you,
into `app/`, day by day. Use this copy to check your own work or as a
fallback if a day's build stalls; don't edit it as part of the live build.

**Read-only, not directly runnable from this location.** These files were
moved here from `app/` and still use `app`-qualified absolute imports
internally (e.g. `from app.paths import ...`) and a hardcoded
`REPO_ROOT / "app" / "outputs"` in `paths.py`. They resolve correctly once
`app/` is populated by the real build (or if you temporarily copy/symlink
this folder to `app/` to run it standalone) — they will not run as
`app_reference.*` as-is. Treat this folder as material to read and compare
against, not to execute in place.

One FNOL-email-resolution pipeline, built up one increment per day across
Week 2. Each `dayN_resolve.py` imports and extends `day(N-1)_resolve.py`,
so Day 1's behavior never silently changes underneath a guide page written
for it — Day 5's file is simply the sum of all five increments.

| Day | File | Adds |
|---|---|---|
| 1 | `day1_resolve.py` | Look up the claim + policy (`claims_lookup.py`, an in-process stdio MCP tool). Draft a grounded reply, or escalate when there's no policy document to ground on (the deliberate `commercial_package` gap) or no claim number at all. |
| 2 | `day2_resolve.py` | Triage/grounding handoff: urgency classification (`bedrock_urgency.py`, live via AWS Bedrock if credentials are set, otherwise a labeled stub) through a deterministic authorization gate, plus an independent re-confirmation of grounding via the Day 2 network-MCP (`claims_network.py`) and A2A (`claims_a2a.py`) lookup logic. |
| 3 | `day3_resolve.py` | Real policy grounding: RAG search over the indexed policy corpus (`rag_index.py`), restricted to the claim's own product docs; an exact-then-semantic cache in front of it (`semantic_cache.py`, hard-partitioned per product — see the note below); a same-address fraud signal from the claims knowledge graph (`graph_signals.py`). |
| 4 | `day4_resolve.py` | Guardrails on the raw inbound email, before any tool call: a prompt-injection scan (`injection_scanner.py`) that blocks and escalates immediately if triggered, and PII redaction (`pii_guardrail.py`) of the body for safe logging. |
| 5 | `day5_resolve.py` | Every decision logged to a persisted, tamper-evident audit chain (`audit_chain.py`); every run gated against the real `claims-triage` governance entry (`autonomy_check.py` — high risk tier, "recommend" autonomy, never "act"); `resolve_all()` runs the whole 12-row inbox and reports a summary. |

## Running it

```bash
uv run python -m app.day1_resolve CLN-001
uv run python -m app.day2_resolve CLN-001
uv run python -m app.day3_resolve CLN-001
uv run python -m app.day4_resolve CLN-001
uv run python -m app.day5_resolve CLN-001
uv run python -m app.day5_resolve --resolve-all
uv run pytest app/test_app.py -v
```

Two servers are real, standalone network services — start them in a
separate terminal (the pipeline itself calls their underlying lookup logic
in-process, but these are the actual network/A2A exercise):

```bash
uv run python -m app.claims_network   # Streamable HTTP MCP, http://127.0.0.1:8766/mcp
uv run python -m app.claims_a2a       # A2A agent, http://127.0.0.1:5055/.well-known/agent.json
```

## Two things worth knowing before you build on this

- **Bedrock is optional, not required.** `day2_resolve.py` calls Bedrock
  only if `AWS_BEARER_TOKEN_BEDROCK` and `BEDROCK_MODEL_ID` are both set;
  otherwise it falls back to a clearly-labeled deterministic stub so the
  rest of the pipeline stays runnable without live AWS access. Check
  `result["urgency_source"]` to see which one actually ran.
- **The semantic cache is namespaced by product on purpose.** An earlier
  version of this pipeline cached RAG answers by question text alone, and
  a paraphrased coverage question for one product returned another
  product's cached policy excerpt — a real cross-grounding bug, caught by
  `test_app.py::test_day3_coverage_excerpt_matches_the_claims_own_product`.
  `semantic_cache.py`'s `get`/`set` now take an explicit `namespace`
  argument (the claim's product) and never match across namespaces.

## What's deliberately not in here

`roi_model.py` (MLflow-tracked ROI estimation) is a related Day 5 exercise
but isn't part of this pipeline — it's a business-metrics side calculation,
not a step in resolving an email, and pulling in MLflow just for this would
be disproportionate. See `W2D5/snippets/roi_model.py`.
