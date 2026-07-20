# Databricks SQL and Spark Processing Assets

This folder contains the ordered managed-platform implementation for catalog creation, incremental ingestion, Silver conformance, dimensional modeling, Gold products, point-in-time features, data quality, and forecast monitoring.

## Execution order

| Order | Asset | Responsibility | Primary outputs |
|---:|---|---|---|
| 00 | `00_catalog_and_schemas.sql` | Creates the target Unity Catalog catalog and required schemas | `bronze`, `silver`, `gold`, `features`, `models`, `semantic`, `ops` |
| 01 | `01_bronze_autoloader.py` | Uses Auto Loader with schema tracking, checkpointing, ingestion timestamps, source files, and batch dates | `bronze.<domain>_raw` |
| 02 | `02_silver_merge.sql` | Casts types, normalizes status values, deduplicates by business key, and performs idempotent Delta `MERGE` | `silver.reservations` reference pattern |
| 03 | `03_dimensional_model.sql` | Builds stable dimensions and atomic facts at declared grains | `gold.dim_*`, `gold.fact_*` |
| 04 | `04_gold_marts.sql` | Publishes resort, campaign, member-points, labor, and semantic products | certified Gold and semantic tables |
| 05 | `05_feature_store.sql` | Builds a leakage-safe member feature product using an explicit as-of cutoff | `features.member_month_features` |
| 06 | `06_quality_and_monitoring.sql` | Persists quality results and forecast accuracy evidence | `ops.data_quality_results`, `ops.waterfall_forecast_accuracy` |

## Runtime parameters

| Parameter | Used by | Meaning |
|---|---|---|
| `catalog` | all SQL assets and ingestion code | active development, staging, or production catalog |
| `as_of_month` | `05_feature_store.sql` | exclusive point-in-time cutoff for feature eligibility |
| `domain` | `01_bronze_autoloader.py` | source domain being incrementally ingested |

Example managed object names:

```text
hospitality_data_platform_dev.bronze.reservations_raw
hospitality_data_platform_staging.features.member_month_features
hospitality_data_platform.gold.resort_monthly_performance
```

## Declared grains

| Product | Grain |
|---|---|
| `gold.dim_member` | one row per member business key |
| `gold.dim_resort` | one row per resort business key |
| `gold.fact_reservation` | one row per reservation |
| `gold.fact_stay` | one row per stay |
| `gold.fact_points_transaction` | one row per points transaction |
| `gold.campaign_tour_sales_attribution` | campaign + channel + market + month |
| `gold.member_points_utilization` | member + month |
| `gold.resort_labor_efficiency` | resort + business date |
| `features.member_month_features` | member + as-of month |
| `ops.waterfall_forecast_accuracy` | model + alias + forecast week + horizon |

## Idempotency and replay

- Auto Loader checkpoints prevent already committed source files from being processed repeatedly.
- Bronze remains source-aligned and retains ingestion metadata for replay and traceability.
- Silver uses business keys and latest-update ordering before `MERGE`.
- Reprocessing the same approved input should converge on the same Silver state.
- Downstream marts aggregate only after grain stabilization, preventing join multiplication.
- Failed quality or model gates should preserve the last successful serving output rather than publishing partial data.

## Data-quality controls

The managed design supports:

- required-column and schema enforcement
- business-key uniqueness
- null-rate thresholds
- referential integrity
- controlled status values
- duplicate-grain detection
- feature cutoff enforcement
- forecast error and bias monitoring

Invalid or breaking source changes should be quarantined or fail publication before dependent feature and model tasks execute.

## Point-in-time feature rules

`05_feature_store.sql` uses the supplied `as_of_month` as an exclusive cutoff:

```text
feature event timestamp < as_of_month
```

The feature product includes member tenure, tier, market, points behavior, stays, room nights, revenue, service cases, escalations, resolution duration, and booking recency. Future outcomes and labels are intentionally excluded from the feature table.

## Recommended deployment sequence

The SQL assets are normally invoked through the Databricks Asset Bundle workflow rather than manually edited notebooks:

```bash
cd databricks
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run hospitality_data_platform_pipeline -t dev
```

Production execution additionally requires approved source volumes, service identities, Unity Catalog grants, cluster policies, network controls, secret management, alerting, and change authorization.

## Target-role evidence

This folder directly demonstrates:

- advanced SQL and Spark SQL
- PySpark streaming ingestion
- Databricks and Delta Lake patterns
- dimensional and lakehouse modeling
- reusable feature construction
- feature-store table design
- schema, missingness, uniqueness, and integrity checks
- feature lineage and event-time correctness
- scalable environment parameterization
