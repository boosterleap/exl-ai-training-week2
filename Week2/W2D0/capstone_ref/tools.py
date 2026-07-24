"""Phase 2 grounding tools for the Bank Loan Approval Assistant.

Two small, clearly-named tools, mirroring W2D1/snippets/insurance_lookup_server.py's
get_claim_and_policy pattern: a structured DB lookup that reports whether grounding
is even available, and a policy-doc search restricted to what's actually on disk.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "loans.db"
POLICIES_DIR = DATA_DIR / "policies"

PRODUCT_TO_POLICY_PREFIX = {
    "home_loan": "LOAN-HOME-010",
    "personal_loan": "LOAN-PERSONAL-020",
    "business_loan": "LOAN-BUSINESS-030",
    "education_loan": "LOAN-EDU-040",
    # gold_loan: deliberate gap -- no entry on purpose, see data/_CAPSTONE_DATA_README.md
}


@dataclass
class LoanRecord:
    loan_id: str
    stage: str | None
    product: str
    loan_amount: float | None
    loan_amount_term: float | None
    applicant_income: float
    coapplicant_income: float
    credit_history: float | None
    self_employed: str | None
    property_area: str
    dependents: str | None
    grounding_available: bool
    policy_doc_files: list[str] = field(default_factory=list)


def get_loan_record(loan_id: str) -> LoanRecord:
    """Look up a loan application and report which policy doc (if any) grounds it.

    If grounding_available is False, no policy document exists for this
    product -- do not answer an eligibility/coverage question from general
    knowledge; escalate instead.
    """
    loan_id = loan_id.strip().upper()
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT l.Loan_ID, l.stage, l.product, l.LoanAmount, l.Loan_Amount_Term,
                   a.ApplicantIncome, a.CoapplicantIncome, a.Credit_History,
                   a.Self_Employed, a.Property_Area, a.Dependents
            FROM loans l JOIN applicants a ON l.Loan_ID = a.Loan_ID
            WHERE l.Loan_ID = ?
            """,
            (loan_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError(f"loan_id {loan_id!r} was not found in loans.db.")

    (lid, stage, product, amount, term, inc, coinc, credit, self_emp, area, deps) = row
    prefix = PRODUCT_TO_POLICY_PREFIX.get(product)
    doc_files = sorted(p.name for p in POLICIES_DIR.glob(f"{prefix}_*.md")) if prefix else []

    return LoanRecord(
        loan_id=lid, stage=stage, product=product, loan_amount=amount,
        loan_amount_term=term, applicant_income=inc, coapplicant_income=coinc,
        credit_history=credit, self_employed=self_emp, property_area=area,
        dependents=deps, grounding_available=bool(doc_files), policy_doc_files=doc_files,
    )


def _chunk_markdown(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading = section.splitlines()[0].lstrip("# ").strip()
        chunks.append({"text": section, "heading": heading, "source_file": path.name})
    return chunks


_embedder = None
_chunks: list[dict] | None = None
_chunk_vectors = None


def _load_index():
    global _embedder, _chunks, _chunk_vectors
    if _chunks is not None:
        return
    import numpy as np
    from sentence_transformers import SentenceTransformer

    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    _chunks = []
    for md_file in sorted(POLICIES_DIR.glob("*.md")):
        _chunks.extend(_chunk_markdown(md_file))
    _chunk_vectors = np.array(_embedder.encode([c["text"] for c in _chunks]))


def search_policy(query: str, k: int = 3, product: str | None = None) -> list[dict]:
    """Semantic search over the underwriting policy docs that exist on disk.

    Pass `product` (from get_loan_record's `product` field) to restrict the
    search to that product's document -- with only 4 short docs total, an
    unscoped search can return a plausible-looking but wrong-product chunk.
    Only home/personal/business/education loan have a document; there is
    nothing to find for gold_loan, by design -- callers should check
    get_loan_record's grounding_available flag before calling this at all.
    """
    import numpy as np

    _load_index()
    prefix = PRODUCT_TO_POLICY_PREFIX.get(product) if product else None
    candidates = (
        [c for c in _chunks if c["source_file"].startswith(prefix)] if prefix else _chunks
    )
    if not candidates:
        return []
    idx_map = [i for i, c in enumerate(_chunks) if c in candidates]
    qvec = np.array(_embedder.encode([query])[0])
    vecs = _chunk_vectors[idx_map]
    sims = vecs @ qvec / (np.linalg.norm(vecs, axis=1) * np.linalg.norm(qvec) + 1e-9)
    top_local = np.argsort(-sims)[:k]
    return [
        {
            "source_file": _chunks[idx_map[i]]["source_file"],
            "heading": _chunks[idx_map[i]]["heading"],
            "text": _chunks[idx_map[i]]["text"],
            "score": float(sims[i]),
        }
        for i in top_local
    ]


if __name__ == "__main__":
    print(get_loan_record("LP002305"))
    print(get_loan_record("LP002448"))  # gold_loan -- grounding_available should be False
    for hit in search_policy("is there a surcharge for rural properties", product="home_loan"):
        print(f"{hit['score']:.3f}  {hit['source_file']} :: {hit['heading']}")
