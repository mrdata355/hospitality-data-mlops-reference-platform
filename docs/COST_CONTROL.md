# Cost Control Plan

## Default demonstration

- Run all data generation, transformations, model training, scoring, API tests, and monitoring locally.
- Use SQLite and CSV for the local execution path.
- Store model artifacts on the local file system.
- Use Docker Desktop only when a container demonstration is required.

## Databricks deployment controls

- Use job clusters instead of always-on interactive clusters.
- Enable auto-termination and autoscaling.
- Process only new or changed files with Auto Loader and checkpoints.
- MERGE only affected partitions.
- Materialize compact Gold tables for BI instead of repeatedly scanning Silver.
- Retrain only when drift, accuracy, freshness, or schedule rules require it.
- Use small development datasets and production-like schemas in dev.
- Apply cluster policies and environment-specific resource limits.

## Serving decision

- Use batch scoring for waterfall forecasts and daily member propensity scores.
- Use Databricks Model Serving only when low-latency access is required.
- Use AKS only when custom networking, runtime, autoscaling, or service-control requirements justify the additional operational cost.
