# ADR 0002: Enforce Point-in-Time Feature Correctness

## Status
Accepted

## Decision
Every time-aware feature calculation ends before the prediction cutoff. Labels are calculated outside the feature window.

## Rationale
This prevents target leakage and makes offline evaluation representative of production scoring.

## Consequences
Feature tables require an entity key and as-of field. Backfills and training joins must preserve event-time semantics.
