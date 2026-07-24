# LOAN-HOME-010 Home Loan Underwriting Policy

Product: home_loan
Effective: 2026-01-01

## Eligibility

Applicants must have a recorded Credit_History value of 1 (a documented history of
timely repayment on prior debt). Applicants with Credit_History 0 or missing are
declined for home_loan pending a manual underwriter review — the automated assistant
must not approve or deny these itself.

## Income-to-installment ratio

Combined monthly obligations (estimated as LoanAmount \* 1000 / Loan_Amount_Term) must
not exceed 40% of combined monthly income (ApplicantIncome + CoapplicantIncome). Cases
above this ratio are routed to manual underwriting, not auto-approved.

## Property area risk tiers

- Urban: standard terms, no surcharge.
- Semiurban: standard terms, no surcharge.
- Rural: a 0.25 percentage-point rate surcharge applies due to lower comparable-sale
  data availability; this does not change eligibility, only the quoted rate.

## Documentation checklist

Identity proof, address proof, last 3 months of income statements, and property title
documents. A case sits in `document_pending` until all four are received; the
assistant may confirm which documents are outstanding but must not estimate a
decision timeline beyond the standard SLA below.

## Processing SLA

Standard decision turnaround is 10 business days from the date all documentation is
received. This SLA is a target, not a contractual guarantee.
