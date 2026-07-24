"""Phase 3 reference: split the single Phase 2 agent into two roles plus an
orchestrator -- an intake/classifier subagent (cheap, structured, one call)
and the Phase 2 underwriting subagent (the grounded tool-use loop), matching
the classifier's output against the email's ground-truth category and
routing to the underwriting subagent for the actual grounded reply.

Run it:
    "C:\\Users\\Asus\\.venv\\Scripts\\python.exe" W2D0/capstone_ref/multiagent.py
"""
from __future__ import annotations

import json
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv

from agent_loop import process_email

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

CLASSIFIER_MODEL = "claude-opus-4-8"
DATA_DIR = Path(__file__).parent / "data"
OUT_DIR = Path(__file__).parent / "outputs"

CATEGORIES = [
    "status_inquiry", "rate_query", "rejection_appeal",
    "document_submission", "fraud_escalation",
]

CLASSIFIER_SYSTEM = """You are the intake subagent for a loan-servicing \
mailbox. Read one customer email and extract its Loan_ID and its category. \
Do not answer the customer's question -- that is a different subagent's job."""

CLASSIFY_TOOL = {
    "name": "classify_email",
    "description": "Record the extracted Loan_ID and category for this email.",
    "input_schema": {
        "type": "object",
        "properties": {
            "loan_id": {"type": "string"},
            "category": {"type": "string", "enum": CATEGORIES},
        },
        "required": ["loan_id", "category"],
    },
}


def classify_email(client: anthropic.Anthropic, subject: str, body: str) -> dict:
    # Force the tool call rather than parsing free text -- a forced tool_choice
    # is the older SDK's structured-output equivalent (this venv's anthropic
    # SDK predates the newer output_config.format parameter).
    response = client.messages.create(
        model=CLASSIFIER_MODEL, max_tokens=256, system=CLASSIFIER_SYSTEM,
        tools=[CLASSIFY_TOOL], tool_choice={"type": "tool", "name": "classify_email"},
        messages=[{"role": "user", "content": f"Subject: {subject}\n\n{body}"}],
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    return tool_use.input


def main():
    client = anthropic.Anthropic()
    emails = pd.read_csv(DATA_DIR / "inbound_emails.csv")
    OUT_DIR.mkdir(exist_ok=True)

    results = []
    correct_category = 0
    correct_loan_id = 0
    for _, row in emails.iterrows():
        classified = classify_email(client, row["subject"], row["body"])
        category_ok = classified["category"] == row["email_category"]
        loan_id_ok = classified["loan_id"].strip().upper() == row["loan_id_ground_truth"]
        correct_category += category_ok
        correct_loan_id += loan_id_ok

        # Orchestrator hands off to the Phase 2 underwriting subagent using
        # the classifier's own extracted loan_id, not the CSV ground truth --
        # this is the real multi-agent handoff, not a shortcut.
        underwriting_result = process_email(client, row["subject"], row["body"])

        results.append({
            "email_id": row["email_id"],
            "classifier_category": classified["category"],
            "category_ground_truth": row["email_category"],
            "category_correct": category_ok,
            "classifier_loan_id": classified["loan_id"],
            "loan_id_correct": loan_id_ok,
            "underwriting_reply": underwriting_result,
        })
        print(f"{row['email_id']}: classifier={classified['category']:20s} "
              f"(truth={row['email_category']:20s}) "
              f"loan_id_match={loan_id_ok} escalated={underwriting_result.get('escalated')}")

    with open(OUT_DIR / "multiagent_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    n = len(emails)
    print(f"\nClassifier category accuracy: {correct_category}/{n}")
    print(f"Classifier loan_id extraction accuracy: {correct_loan_id}/{n}")


if __name__ == "__main__":
    main()
