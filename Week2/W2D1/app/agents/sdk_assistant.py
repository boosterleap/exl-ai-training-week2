"""Claude Agent SDK Day 1 assistant shape (study only)."""

from __future__ import annotations

from .. import config
from ..models import TriageDecision
from ..permissions.gates import WRITE_TOOLS, approval_required


SYSTEM = """
You are the Day 1 operations assistant for insurance FNOL and logistics holds.
Use domain tools for facts. Never invent claim, policy, or shipment records.
Write tools require learner approval and an idempotency key.
Return a valid TriageDecision when asked.
""".strip()


def build_options(*, model: str | None = None, permission_mode: str = "default"):
    """Study shape for ClaudeAgentOptions fields used on Day 1."""
    return {
        "model": model or config.DEFAULT_MODEL,
        "system_prompt": SYSTEM,
        "allowed_tools": [
            "mcp__ops__fnol_lookup",
            "mcp__ops__claim_lookup",
            "mcp__ops__policy_lookup",
            "mcp__ops__shipment_lookup",
            "mcp__ops__release_hold",
        ],
        "permission_mode": permission_mode,
        "max_turns": config.MAX_TURNS,
        "max_budget_usd": config.MAX_BUDGET_USD,
    }


async def run_query(prompt: str, options: dict):
    """Study stub for query()-style one-shot runs."""
    return {"prompt": prompt, "options": options, "mode": "query"}


async def run_client_session(session_id: str, prompts: list[str], options: dict):
    """Study stub for ClaudeSDKClient multi-turn sessions."""
    return {
        "session_id": session_id,
        "prompts": prompts,
        "options": options,
        "mode": "client",
        "writes_need_approval": [tool for tool in WRITE_TOOLS if approval_required(tool)],
    }


def parse_decision(payload: dict) -> TriageDecision:
    return TriageDecision.model_validate(payload)
