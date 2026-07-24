"""Phase 2 reference: a single-agent tool-use loop that drafts grounded, cited
replies to the 12 inbound emails -- and explicitly escalates on the 3 gold_loan
(no-policy) cases instead of inventing an eligibility rule.

Run it:
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/agent_loop.py
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

from tools import get_loan_record, search_policy

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MODEL = "claude-opus-4-8"
DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "outputs"

SYSTEM_PROMPT = """You are a bank loan-servicing assistant. You draft replies to \
inbound customer emails about their loan applications.

Ground rules (never break these):
1. Never invent a policy term, ratio, surcharge, SLA, or decision status. Every \
factual claim in your reply must come from a tool result you actually called.
2. Always call get_loan_record first to find the loan's current stage and product, \
and whether grounding_available is true.
3. If grounding_available is false, do NOT call search_policy for that loan, and do \
NOT answer any eligibility/rate/criteria question from general knowledge. Instead \
draft a reply that tells the customer their case is being escalated to a human \
underwriter because policy terms for their product are not available to you.
4. If grounding_available is true and the question concerns policy terms (ratios, \
surcharges, documents, SLA), call search_policy (pass the loan's product) and cite \
the specific policy document filename in your reply.
5. Never state or imply a final approve/deny decision yourself -- you may report the \
current stage, but any decision framing belongs to a human underwriter.

After drafting, your FINAL message must contain ONLY a JSON object (no prose \
before or after it, no markdown code fences) with keys: "reply" (string), \
"escalated" (bool, true if this case needed human escalation because grounding was \
unavailable), "cited_sources" (list of policy filenames actually cited, empty if none)."""

TOOLS = [
    {
        "name": "get_loan_record",
        "description": "Look up a loan application by Loan_ID.",
        "input_schema": {
            "type": "object",
            "properties": {"loan_id": {"type": "string"}},
            "required": ["loan_id"],
        },
    },
    {
        "name": "search_policy",
        "description": "Semantic search over underwriting policy docs, scoped to one product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "product": {"type": "string"},
            },
            "required": ["query", "product"],
        },
    },
]


TRACE_LOG_PATH = OUT_DIR / "tool_trace.jsonl"


def run_tool(name: str, tool_input: dict) -> dict:
    if name == "get_loan_record":
        return asdict(get_loan_record(tool_input["loan_id"]))
    if name == "search_policy":
        return {"hits": search_policy(tool_input["query"], product=tool_input.get("product"))}
    raise ValueError(f"Unknown tool {name}")


def _log_tool_call(email_id: str | None, tool: str, arguments: dict, duration_ms: float) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    entry = {"email_id": email_id, "tool": tool, "arguments": arguments, "duration_ms": round(duration_ms, 1)}
    with open(TRACE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def process_email(client: anthropic.Anthropic, subject: str, body: str, email_id: str | None = None) -> dict:
    messages = [
        {"role": "user", "content": f"Subject: {subject}\n\n{body}"},
    ]
    for _ in range(6):  # bounded agentic loop
        response = client.messages.create(
            model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT,
            tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            break
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                start = time.perf_counter()
                try:
                    result = run_tool(block.name, block.input)
                except Exception as exc:  # noqa: BLE001
                    result = {"error": str(exc)}
                _log_tool_call(email_id, block.name, block.input, (time.perf_counter() - start) * 1000)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
                )
        messages.append({"role": "user", "content": tool_results})

    final_text = "".join(b.text for b in response.content if b.type == "text")
    parsed = extract_json_object(final_text)
    if parsed is None:
        parsed = {"reply": final_text, "escalated": None, "cited_sources": []}
    return parsed


def extract_json_object(text: str) -> dict | None:
    """Find the last balanced {...} block in text and parse it.

    Models sometimes wrap the requested JSON in reasoning prose or a
    ```json fence despite instructions not to -- rather than relying on
    prompting alone, parse defensively by scanning for the last top-level
    JSON object in the text.
    """
    start = text.rfind("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
        start = text.rfind("{", 0, start)
    return None


def main():
    client = anthropic.Anthropic()
    emails = pd.read_csv(DATA_DIR / "inbound_emails.csv")
    OUT_DIR.mkdir(exist_ok=True)

    TRACE_LOG_PATH.unlink(missing_ok=True)  # fresh trace per run
    results = []
    for _, row in emails.iterrows():
        parsed = process_email(client, row["subject"], row["body"], email_id=row["email_id"])
        parsed["email_id"] = row["email_id"]
        parsed["loan_id"] = row["loan_id_ground_truth"]
        parsed["product"] = row["product_ground_truth"]
        results.append(parsed)
        print(f"{row['email_id']} ({row['product_ground_truth']}) -> "
              f"escalated={parsed.get('escalated')} cited={parsed.get('cited_sources')}")

    with open(OUT_DIR / "draft_replies.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    gold_cases = [r for r in results if r["product"] == "gold_loan"]
    correctly_escalated = sum(1 for r in gold_cases if r.get("escalated") is True)
    fabricated = sum(1 for r in gold_cases if r.get("cited_sources"))
    print(f"\ngold_loan cases: {len(gold_cases)}, correctly escalated: {correctly_escalated}, "
          f"fabricated a citation: {fabricated}")


if __name__ == "__main__":
    main()
