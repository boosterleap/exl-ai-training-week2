# LOAN-PERSONAL-020 Personal Loan Underwriting Policy

Product: personal_loan
Effective: 2026-01-01

## Eligibility

Personal loans require Credit_History of 1. Unlike home_loan, there is no property
collateral, so applicants with Credit_History 0 are declined outright rather than
routed to manual review — this is a firm rule, not a discretionary one.

## Income-to-installment ratio

Combined monthly obligations (estimated as LoanAmount \* 1000 / Loan_Amount_Term) must
not exceed 35% of combined monthly income (ApplicantIncome + CoapplicantIncome), a
stricter floor than home_loan's 40% because there is no collateral to recover value
from on default.

## Dependents surcharge

Applicants with 3+ Dependents receive a 0.15 percentage-point rate surcharge to
reflect higher household expense load. This does not affect eligibility.

## Documentation checklist

Identity proof, address proof, and last 3 months of income statements. No property
documents are required since personal_loan is unsecured.

## Processing SLA

Standard decision turnaround is 3 business days from the date all documentation is
received — faster than home_loan because there is no title/property verification
step.
