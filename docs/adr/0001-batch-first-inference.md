# ADR 0001: Use Batch Inference as the Default

## Status
Accepted

## Decision
Forecasts and broad member score refreshes use scheduled batch inference. Online serving is reserved for interactions that require low-latency decisions.

## Rationale
Batch scoring is less expensive, easier to replay, simpler to audit, and naturally aligned with BI and planning outputs. It also avoids paying for an always-on endpoint when no real-time requirement exists.

## Consequences
The platform must publish score tables on a defined freshness schedule. Use cases requiring synchronous decisions need a separate latency and availability review.
