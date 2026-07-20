# Production-Style System Design

## System objective

This independent reference platform standardizes resort, reservation, member, points, marketing, tour, contract, service, and labor data into governed analytical and machine-learning products. Reporting and model features use the same conformed facts and dimensions so business definitions are not recreated across notebooks, dashboards, and APIs.

## Architecture layers

1. **Landing and Bronze:** immutable source delivery, file lineage, batch IDs, ingestion timestamps, and record hashes.
2. **Silver:** schema enforcement, type normalization, latest-record deduplication, controlled status values, foreign-key validation, and quarantine behavior.
3. **Conformed model:** stable member, resort, campaign, and date dimensions plus atomic reservation, stay, points, tour, contract, service, labor, and marketing facts.
4. **Gold products:** resort performance, campaign-to-contract attribution, member points utilization, labor efficiency, and governed semantic metrics.
5. **Feature products:** point-in-time member-month features and resort-week forecasting features.
6. **Model systems:** reproducible training, chronological validation, acceptance gates, immutable model versions, and controlled MLflow aliases.
7. **Serving:** batch scoring by default, optional FastAPI synchronous scoring, Docker, and Kubernetes.
8. **Operations:** freshness, data quality, drift, accuracy, latency, cost, rollback, incident response, and audit evidence.

## Primary architecture decisions

| Decision | Operational effect |
|---|---|
| Batch-first inference | Reduces cost and simplifies replay, audit, and BI consumption. |
| Immutable landing and replayable Bronze | Enables deterministic recovery without requiring upstream teams to recreate prior deliveries. |
| Declared fact grains | Prevents duplicate multiplication and unstable business metrics. |
| Point-in-time feature cutoffs | Prevents target leakage and preserves training-serving consistency. |
| Last-successful publication | A failed run cannot replace the prior validated Gold, feature, score, or forecast output. |
| MLflow alias promotion | Production changes through controlled alias movement rather than mutable model replacement. |
| Separate liveness and readiness | Unready pods leave service before process restart, preventing traffic to an unloaded model. |

## Model acceptance

The member-risk workflow requires a minimum approved ROC AUC. The resort-week forecast uses chronological validation and must satisfy both an absolute WAPE threshold and comparison with a 52-week seasonal baseline before promotion. Rejected candidates leave the current `Champion` alias unchanged.

## Environment strategy

Databricks Asset Bundle targets inject separate Unity Catalog catalogs for development, staging, and production. Local validation uses generated fixtures and requires no recurring cloud spend. Authorized production deployment requires approved source connections, identities, credentials, security review, and change approval.

## Recovery model

Source replay begins from immutable landing data. Only affected Silver keys or partitions and their dependent Gold/features are rebuilt. Model rollback moves the production alias to the last approved version, verifies schema and score behavior, and records the failed version, impact window, and completion evidence.
