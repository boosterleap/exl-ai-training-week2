"""Permission gates for Day 1 write tools."""

from __future__ import annotations

WRITE_TOOLS = {"release_hold", "mcp__ops__release_hold"}


def approval_required(tool_name: str) -> bool:
    return tool_name in WRITE_TOOLS


def can_run_write(*, tool_name: str, approved: bool, idempotency_key: str) -> bool:
    if tool_name not in WRITE_TOOLS:
        return True
    return approved and bool(idempotency_key)


def filter_allowed(requested: list[str], allowed: list[str]) -> list[str]:
    allowed_set = set(allowed)
    return [name for name in requested if name in allowed_set]
