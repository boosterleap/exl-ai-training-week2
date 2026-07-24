# LOAN-EDU-040 Education Loan Underwriting Policy

Product: education_loan
Effective: 2026-01-01

## Eligibility

Education loans use a relaxed credit-history rule relative to other unsecured
products: applicants with Credit_History 0 or missing are still eligible for
automated processing provided a Co-applicant is present (CoapplicantIncome > 0),
since the co-applicant (typically a parent/guardian) is treated as a secondary
repayment source. Applicants with Credit_History 0/missing AND no co-applicant are
routed to manual underwriting.

## Income-to-installment ratio

Combined monthly obligations (estimated as LoanAmount \* 1000 / Loan_Amount_Term) must
not exceed 45% of combined monthly income — the most permissive ratio of the four
documented products, reflecting the deferred-repayment structure typical of
education loans.

## Documentation checklist

Identity proof, address proof, admission or enrollment confirmation from the
educational institution, and co-applicant income proof if a co-applicant is listed.

## Processing SLA

Standard decision turnaround is 5 business days from the date all documentation is
received.
