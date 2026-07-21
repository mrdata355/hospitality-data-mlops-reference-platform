# Executive Overview

## Hospitality Data and MLOps Reference Platform

**Designed and implemented by Kellon Lewis**

This independent reference implementation demonstrates how a hospitality organization can connect governed operational data, reusable analytical products, point-in-time features, controlled model delivery, and observable serving without exposing customer records or credentials.

## Business problem

Hospitality decisions are often split across reservation, member, points, marketing, tour, contract, labor, service, and resort systems. The platform establishes stable grains and contracts across those domains so analytics, forecasting, and risk scoring can share the same governed foundation.

## Implemented system

The repository implements the path from deterministic source generation through Bronze and Silver processing, conformed dimensions and atomic facts, Gold products, point-in-time features, model training, acceptance gates, MLflow registration and alias control, batch scoring, secured API serving, monitoring, rollback, and incident response.

It also validates the running container rather than treating successful unit tests as sufficient release evidence.

## Verified evidence

| Evidence | Result |
|---|---:|
| Member-risk ROC AUC | `0.810+` |
| Resort-week forecast WAPE | `0.249` |
| Seasonal baseline WAPE | `0.265` |
| Source domains represented | `12` |
| Reservation rows | `28,000` |
| Labor-shift rows | `40,866` |
| Serving release gate | Build, restricted run, readiness, score, metrics, benchmark |
| Forecast robustness | Expanding-window rolling-origin backtest artifact |
| Software assurance | Ruff, branch coverage, dependency audit, CodeQL |
| System validation | One command produces data, model, temporal, API, and metrics evidence |

The model measurements are deterministic system-validation evidence produced from generated data. They are not claims of customer impact or real-world predictive lift.

## Key engineering decisions

- Batch-first inference is the default because it lowers cost and simplifies replay, audit, and downstream consumption.
- Every fact, feature table, and analytical product declares its grain before aggregation.
- Feature windows end before prediction cutoffs to prevent target leakage.
- Forecast candidates must pass an absolute WAPE threshold and beat the seasonal baseline before alias promotion.
- The active model is changed only after objective validation; the previous version remains available for rollback.
- Development, staging, and production use separate Unity Catalog catalog variables.
- The local path remains reproducible without recurring cloud spend or embedded credentials.
- Exact direct dependency versions, dependency auditing, static analysis, coverage, and automated update proposals reduce software-supply-chain drift.

## Validation path

```bash
make system-validation
```

The command regenerates the platform, executes rolling-origin validation, starts the restricted container, validates the live API contract, records machine-readable evidence, and stops the container. The operational procedure is documented in `docs/SYSTEM_VALIDATION.md`.

## Material boundaries

The local data, model, API, Docker, testing, benchmarking, and CI paths are executable without cloud credentials. The Azure, Databricks, Unity Catalog, MLflow Registry, and Kubernetes assets are implementation-ready definitions, not evidence of an active deployment inside a real company.

The manual Azure workflow can create sanitized deployment evidence after an authorized OpenID Connect identity and dedicated Azure resources are configured. Until that workflow completes successfully, no live Azure deployment is claimed.

A production authorization would still require approved identities, networking, source contracts, secrets, registry access, production-like volume tests, monitoring destinations, data-owner acceptance, and operational sign-off.

## Validation commands

```bash
make validate
make quality
make security
make system-validation
```
