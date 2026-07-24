# Capstone data — Bank Loan Approval Assistant

Same shape as the week's insurance/logistics threads (`data/_DATA_README.md`), applied to
a new domain: an assistant that resolves inbound loan-applicant emails by grounding every
statement in a real record and a specific policy document — never inventing a term.

## Source

`loans.db` is seeded from the real, public **Analytics Vidhya Loan Prediction** dataset
(`seed_loans_db.py`, reachable at
`https://raw.githubusercontent.com/dphi-official/Datasets/master/Loan_Data/loan_train.csv`).
The raw file has **491 unique `Loan_ID` rows**, 13 source columns, and realistic missing
data (43 rows missing `Credit_History`, 16 missing `LoanAmount`, 29 missing
`Self_Employed`, etc.) — this is genuine messiness from a public dataset, not synthesized.

## Schema

| File | What it is |
|---|---|
| `loans.db` (SQLite: `applicants`, `loans`) | Structured lookup — a tool call resolves `Loan_ID` against this |
| `policies/*.md` | 4 underwriting policy docs (one per documented product) — the RAG corpus |
| `inbound_emails.csv` | 12 inbound customer emails to triage/respond to (ground-truth category, urgency, loan ID, route queue, product, and expected grounded action) |

`applicants`: `Loan_ID, Gender, Married, Dependents, Education, Self_Employed,
ApplicantIncome, CoapplicantIncome, Credit_History, Property_Area`

`loans`: `Loan_ID, LoanAmount, Loan_Amount_Term, product, historical_status, stage`

- `product` is assigned deterministically per `Loan_ID` (sha256-based hash across the 5
  products below), so re-seeding is stable.
- `historical_status` (`approved`/`rejected`) comes from the dataset's original
  `Loan_Status` column — background signal only, not the live case state.
- `stage` is non-null for exactly the **12 live cases** referenced by
  `inbound_emails.csv` (`under_review`, `approved`, `rejected`, `document_pending`,
  `escalated_fraud_review`); all other 479 rows have `stage = NULL` and exist purely as
  richer lookup/background data.

## Product → policy doc mapping

| `product` | Policy doc | Live cases |
|---|---|---|
| `home_loan` | `LOAN-HOME-010_underwriting.md` | LP001715, LP002209, LP002113 |
| `personal_loan` | `LOAN-PERSONAL-020_underwriting.md` | *(none of the 12 live cases — reserved, same role as insurance's `health` product)* |
| `business_loan` | `LOAN-BUSINESS-030_underwriting.md` | LP002305, LP001136, LP001577, LP001849 |
| `education_loan` | `LOAN-EDU-040_underwriting.md` | LP001318, LP002086 |
| `gold_loan` | **none — deliberate gap** | LP001493, LP002448, LP001091 |

`gold_loan` has **no matching policy doc on purpose** — the loan-domain parallel to
insurance's `commercial_package` gap and logistics' `air` gap. Three of the 12 live
cases are `gold_loan` (`LP001493`, `LP002448`, `LP001091`) specifically so the assistant
gets repeated practice recognizing "I have no grounding for this product" and escalating
instead of fabricating an underwriting rule. `LP001091` additionally doubles as the
fraud-review case (`LN-012`), mirroring the insurance claim's fraud angle
(`CLN-012`/`CLM-255335`).

## Known data-quality wrinkles (deliberate, not bugs)

- `LP002113` (live, rejected, home_loan) has a missing `LoanAmount` — the assistant must
  say so rather than inventing a figure when asked to justify the rejection numerically.
- `LP001091` (live, escalated_fraud_review, gold_loan) has both `Credit_History` and
  `Self_Employed` missing, on top of having no policy doc — intentionally the hardest
  grounding case in the set.

## Regenerating the database

```bash
"C:\Users\Asus\.venv\Scripts\python.exe" W2D0/capstone_ref/data/seed_loans_db.py
```

Re-run at any point to reset `loans.db` to its original seed state (network access
required — it re-fetches the source CSV each time, same pattern as
`data/insurance/seed_claims_db.py`).
