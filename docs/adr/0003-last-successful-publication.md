# ADR 0003: Preserve the Last Successful Serving Version

## Status
Accepted

## Decision
A failed upstream run cannot replace the last successful Gold, feature, score, or forecast partition.

## Rationale
Serving stale but validated data is safer than publishing incomplete or invalid data without an explicit business decision.

## Consequences
Freshness alerts must clearly distinguish stale data from unavailable data. Recovery procedures must replay the affected partition and republish atomically.
