"""Permission-policy tests for the Day 1 study app gates."""

from __future__ import annotations

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from app.permissions.gates import can_run_write  # noqa: E402


def test_write_requires_approval() -> None:
    assert not can_run_write(
        tool_name="release_hold",
        approved=False,
        idempotency_key="release-001",
    )


def test_write_requires_nonempty_key() -> None:
    assert not can_run_write(
        tool_name="release_hold",
        approved=True,
        idempotency_key="",
    )


def test_approved_write_with_key_passes() -> None:
    assert can_run_write(
        tool_name="release_hold",
        approved=True,
        idempotency_key="release-001",
    )


def test_read_tools_do_not_need_write_gate() -> None:
    assert can_run_write(
        tool_name="fnol_lookup",
        approved=False,
        idempotency_key="",
    )
