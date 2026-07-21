# Platform Components

This repository implements one connected production-style hospitality data and MLOps platform composed of six bounded engineering domains. Each domain has defined responsibilities, data products, and interfaces to adjacent components.

## 1. Lakehouse Foundation

**Responsibilities:** Replayable Bronze ingestion, Silver conformance, schema enforcement, data contracts, quality gates, conformed dimensions, atomic facts, and Gold publication.

**Primary outputs:** Governed Delta-style tables, dimensional models, quality results, curated marts, and reusable source products for downstream analytics and machine learning.

## 2. Tour and Contract Attribution

**Responsibilities:** Package-to-tour-to-show-to-contract funnel modeling with controlled grain, campaign attribution, conversion metrics, contract value, and return-on-ad-spend calculation.

**Primary outputs:** Reconciled funnel facts, campaign performance products, conversion measures, attribution-ready dimensions, and governed self-service KPI definitions.

## 3. Member Points and Risk

**Responsibilities:** Point-in-time member feature construction, points-utilization measures, service-friction signals, churn-risk classification, batch scoring, and synchronous API scoring.

**Primary outputs:** Versioned member feature products, model-ready datasets, batch predictions, online inference contracts, feature documentation, and quality checks.

## 4. Resort-Week Demand Forecasting

**Responsibilities:** Leakage-safe lag and rolling feature generation, chronological validation, seasonal-baseline comparison, model acceptance gates, forecast publication, monitoring, promotion, and rollback.

**Primary outputs:** Resort-week feature tables, validated forecast candidates, published forecasts, error metrics, MLflow lifecycle records, and rollback-ready model versions.

## 5. Resort Labor Efficiency

**Responsibilities:** Resort-day demand and staffing alignment, payroll cost per occupied unit, revenue per labor hour, and staffing anomaly detection.

**Primary outputs:** Governed labor-efficiency marts, staffing variance indicators, anomaly signals, and operational metrics that connect demand patterns to workforce planning.

## 6. Production MLOps Control Plane

**Responsibilities:** CI/CD, Databricks Asset Bundles, MLflow model registration and alias promotion, artifact versioning, batch scoring, FastAPI serving, Docker, Kubernetes, observability, rollback, SLOs, and incident response.

**Primary outputs:** Reproducible builds, validated model artifacts, versioned serving images, deployment definitions, runtime telemetry, release evidence, and operational runbooks.

## Integration Model

The six domains operate as one system through shared source contracts, conformed dimensions, feature definitions, model lifecycle controls, serving interfaces, data-quality standards, and observability conventions. Changes in one domain are validated against downstream dependencies through automated tests and release gates.
