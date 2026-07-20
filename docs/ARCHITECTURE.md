# System Architecture

## Purpose

The platform standardizes ingestion, conformance, dimensional modeling, analytical serving, feature engineering, model training, scoring, and monitoring for resort and membership data products. The design keeps reporting logic and machine learning inputs on the same governed data backbone.

## Logical layers

| Layer | Responsibility | Persistence |
|---|---|---|
| Landing | immutable source delivery and file-level audit | cloud object storage or local test fixtures |
| Bronze | source-aligned records with ingestion metadata | Delta tables or CSV fixtures |
| Silver | typed, deduplicated, validated business entities | Delta tables or conformed CSV |
| Gold atomic | dimensions and facts at declared grains | Delta tables and SQLite for local validation |
| Gold serving | business marts and semantic metrics | Delta tables, SQL warehouse, BI tools |
| Features | point-in-time model inputs | Unity Catalog feature tables or local CSV |
| Models | trained artifacts, signatures, metrics, aliases | MLflow Models in Unity Catalog or joblib locally |
| Serving | batch prediction tables and optional REST endpoint | Delta output tables, Databricks serving, or AKS |
| Operations | quality, drift, accuracy, latency, freshness, incidents | operations schema and monitoring platform |

## Data flow

1. Each landed file receives `_source_file`, `_batch_id`, `_ingested_at`, and `_record_hash`.
2. Silver transformations normalize types and status values, select the latest business-key record, and reject invalid foreign keys.
3. Conformed dimensions assign stable surrogate keys. Atomic facts retain the lowest useful business grain.
4. Gold marts aggregate only after the fact grain is stable.
5. Feature jobs apply event-time cutoffs before calculating rolling windows.
6. Training jobs log parameters, metrics, feature lists, code version, model signature, and artifacts.
7. Accepted models are assigned a controlled alias and used by batch or online scoring jobs.
8. Monitoring joins predictions to actual outcomes and records accuracy, drift, freshness, volume, and runtime status.

## Dimensional model

### Dimensions

- `dim_member`: member identifier, tier, home market, tenure attributes
- `dim_resort`: resort, market, region, capacity, property type
- `dim_campaign`: campaign, channel, target market, active dates, budget
- `dim_date`: date, fiscal and calendar attributes, weekend indicators

### Facts

- `fact_reservation`: one row per reservation
- `fact_stay`: one row per active or completed stay
- `fact_points_transaction`: one row per points movement
- `fact_tour_event`: one row per tour status event
- `fact_sales_contract`: one row per contract
- `fact_service_case`: one row per service case
- `fact_labor_shift`: one row per employee shift
- `fact_marketing_touch`: one row per marketing touch

## Environment isolation

| Environment | Purpose | Data | Deployment control |
|---|---|---|---|
| local | development and deterministic validation | generated validation fixtures | developer machine or CI runner |
| dev | integration testing | masked or generated non-production data | automatic deployment from feature branches |
| staging | production-like verification | approved non-production data | protected branch and approval gate |
| prod | business workloads | governed production data | release approval, change record, rollback plan |

## Failure boundaries

- A Bronze failure stops only the affected source domain.
- A Silver contract failure prevents downstream publication for that entity.
- Gold marts retain the prior successful version when an upstream job fails.
- Model training failure does not affect the active model alias.
- Scoring failure does not replace the last successful score partition.
- Online serving health and readiness are separated so traffic is removed before the process is restarted.
