---
name: day1-pm-permissions
description: Teach least privilege, hold-release write gates, and ReleaseProposal vs actual write.
disable-model-invocation: true
---

# Day 1 PM — permissions / write boundary

1. Look up shipment `MSKU789` from `Week2/data/logistics/shipment_events.jsonl`.
2. Produce a `ReleaseProposal` JSON only (should_release / reason / source_event_id). Do **not** claim a release executed.
3. List the four write gates:
   - ALLOW_LOCAL_WRITES
   - ALLOW_HOLD_RELEASE
   - LEARNER_APPROVED_HOLD_RELEASE
   - HOLD_RELEASE_IDEMPOTENCY_KEY (12+ chars, non-placeholder)
4. Show `write_skipped: true` unless the instructor explicitly arms all four.
5. Explain `can_use_tool` allow vs deny in operator language.
