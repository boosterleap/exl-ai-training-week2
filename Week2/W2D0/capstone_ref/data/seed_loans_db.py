"""Seed loans.db from the real public Analytics Vidhya Loan Prediction dataset.

Re-runnable: always rebuilds loans.db from scratch (mirrors data/insurance/seed_claims_db.py).
"""
import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent
DB_PATH = DATA_DIR / "loans.db"
SOURCE_URL = "https://raw.githubusercontent.com/dphi-official/Datasets/master/Loan_Data/loan_train.csv"

# Products mapped deterministically from each Loan_ID so re-runs are stable.
# gold_loan is a DELIBERATE grounding gap -- no policy doc exists for it (see policies/).
PRODUCTS = ["home_loan", "personal_loan", "business_loan", "education_loan", "gold_loan"]

# Loan_IDs pinned to specific products/stages so the CP1 email set (written by hand
# against these IDs) stays stable across re-seeds even though hashing is deterministic
# anyway -- kept explicit for clarity, same spirit as insurance's hand-picked David Taylor case.
LIVE_CASE_STAGES = {
    # loan_id: (stage, forced_product_or_None) -- all 12 Loan_IDs verified present in the
    # real dataset (see W2D0/capstone_ref/data/_CAPSTONE_DATA_README.md for the full case list)
    "LP002305": ("approved", None),
    "LP001318": ("approved", None),
    "LP001715": ("under_review", None),
    "LP001493": ("under_review", None),
    "LP002448": ("under_review", "gold_loan"),          # deliberate grounding gap case
    "LP002086": ("rejected", None),
    "LP001849": ("rejected", None),
    "LP001577": ("rejected", None),
    "LP002113": ("rejected", None),
    "LP001136": ("document_pending", None),
    "LP002209": ("document_pending", None),
    "LP001091": ("escalated_fraud_review", "gold_loan"),  # deliberate grounding gap case
}


def product_for(loan_id: str) -> str:
    digest = hashlib.sha256(loan_id.encode()).hexdigest()
    return PRODUCTS[int(digest, 16) % len(PRODUCTS)]


def build():
    print(f"Fetching {SOURCE_URL} ...")
    df = pd.read_csv(SOURCE_URL)
    if df.columns[0].startswith("Unnamed"):
        df = df.drop(columns=[df.columns[0]])
    df = df.dropna(subset=["Loan_ID"]).drop_duplicates(subset=["Loan_ID"])
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    applicants_cols = [
        "Loan_ID", "Gender", "Married", "Dependents", "Education",
        "Self_Employed", "ApplicantIncome", "CoapplicantIncome",
        "Credit_History", "Property_Area",
    ]
    applicants = df[applicants_cols].copy()

    loans = df[["Loan_ID", "LoanAmount", "Loan_Amount_Term", "Loan_Status"]].copy()
    loans["product"] = loans["Loan_ID"].apply(
        lambda lid: LIVE_CASE_STAGES.get(lid, (None, None))[1] or product_for(lid)
    )
    loans["historical_status"] = loans["Loan_Status"].map({"Y": "approved", "N": "rejected"})
    loans["stage"] = loans["Loan_ID"].map(lambda lid: LIVE_CASE_STAGES.get(lid, (None, None))[0])
    loans = loans.drop(columns=["Loan_Status"])

    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    applicants.to_sql("applicants", conn, index=False)
    loans.to_sql("loans", conn, index=False)
    conn.execute("CREATE INDEX idx_loans_product ON loans(product)")
    conn.execute("CREATE INDEX idx_loans_stage ON loans(stage)")
    conn.commit()

    n_live = loans["stage"].notna().sum()
    print(f"Wrote {DB_PATH} -- applicants: {len(applicants)} rows, loans: {len(loans)} rows")
    print(f"Live cases (non-null stage): {n_live}")
    print("Product distribution:\n", loans["product"].value_counts())
    conn.close()


if __name__ == "__main__":
    build()
