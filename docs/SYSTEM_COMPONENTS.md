# System Components

## Lakehouse foundation

Owns source ingestion, lineage metadata, Silver conformance, dimensions, facts, and quality gates. Interfaces are Delta tables in Databricks and CSV/SQLite artifacts in the local engineering environment.

## Tour and contract attribution

Owns package, tour, show, contract, and campaign attribution at a controlled package/prospect grain before campaign aggregation.

## Member points and risk

Owns point-in-time member features, batch member risk scores, model metrics, and API scoring contract.

## Resort-week forecasting

Owns lag and rolling feature generation, time-based validation, seasonal baseline comparison, forecasts, actual alignment, and error monitoring.

## Labor efficiency

Owns resort-day demand and labor alignment, cost-per-occupied-unit, revenue-per-labor-hour, and anomaly flags.

## MLOps control plane

Owns CI/CD, model registry promotion, batch scoring, API packaging, deployment manifests, monitoring, rollback, and operational runbooks.
