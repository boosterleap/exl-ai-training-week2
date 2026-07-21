# OCEAN-SLA-001 Ocean Freight Delay Compensation

Mode: ocean
Effective: 2026-01-01

## Compensation trigger

A delay-compensation credit applies only when the contracted transit window
(see OCEAN-SLA-001 transit times) is missed by more than 48 hours for reasons
within carrier control, such as port congestion caused by the carrier's own
vessel scheduling.

## Excluded causes

Weather rerouting, customs holds, and documentation mismatches are explicitly
excluded from delay compensation, since these are outside carrier control.

## Credit schedule

Eligible delays receive a freight-cost credit of 5% per additional 24-hour period
beyond the 48-hour threshold, capped at 25% of the shipment's freight cost.

## Required evidence

A compensation request must cite the original contracted ETA, the actual
arrival timestamp, and the stated delay reason from the shipment event log.
