# LOAN-BUSINESS-030 Business Loan Underwriting Policy

Product: business_loan
Effective: 2026-01-01

## Eligibility

Business loans are available to both self-employed and salaried applicants, but
Self_Employed = Yes applicants must additionally show Credit_History of 1 AND
combined income (ApplicantIncome + CoapplicantIncome) of at least 4000 to qualify for
automated processing; below that income floor, a self-employed application is routed
to manual underwriting regardless of credit history, since income for self-employed
applicants is treated as less verifiable from the application alone.

## Income-to-installment ratio

Combined monthly obligations (estimated as LoanAmount \* 1000 / Loan_Amount_Term) must
not exceed 40% of combined monthly income.

## Rejection appeal window

An applicant whose business_loan is rejected may request a single re-review within 30
days of the rejection date if they can supply additional income documentation not
present in the original application. The assistant may acknowledge an appeal request
and confirm what documentation would be needed, but the re-review decision itself
requires human underwriter sign-off.

## Documentation checklist

Identity proof, address proof, last 3 months of income statements, and (for
Self_Employed = Yes applicants only) the two most recent years of business tax
filings.

## Processing SLA

Standard decision turnaround is 7 business days from the date all documentation is
received.
