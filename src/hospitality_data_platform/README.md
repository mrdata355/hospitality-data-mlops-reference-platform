# `hospitality_data_platform` Package

This package is the executable local implementation of the hospitality data and MLOps platform. It provides a complete credential-free path from generated sources through analytical products, ML features, trained models, monitoring evidence, and API scoring.

## Module map

| Module | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `config.py` | resolves repository paths, artifact directories, database location, and deterministic seed | repository filesystem | runtime path constants and initialized output folders |
| `data_generation.py` | generates 12 connected synthetic business domains with seasonal, behavioral, funnel, service, and labor relationships | fixed seed | CSV source files under `data/raw/` |
| `pipeline_ingestion.py` | adds Bronze lineage metadata, parses dates, deduplicates latest business-key records, normalizes values, and enforces quality gates | raw CSV source files | `data/bronze/`, `data/silver/`, quality results |
| `pipeline_dimensional.py` | builds conformed dimensions and atomic facts with surrogate keys | Silver entities | dimensions and fact tables under `data/gold/` |
| `pipeline_marts.py` | creates resort, campaign, member-points, labor, and semantic products | Silver entities and conformed model | Gold marts and metric definitions |
| `pipeline.py` | orchestrates Bronze, Silver, dimensional, Gold, and SQLite publication | generated sources | local analytical database and persisted tables |
| `features.py` | builds member-month and resort-week point-in-time feature products | Silver entities | feature CSVs under `data/gold/` |
| `models.py` | trains the member-risk classifier and resort-week forecast, evaluates gates, and writes predictions | feature products | joblib models, metrics, scores, forecasts |
| `monitoring.py` | evaluates feature drift, forecast accuracy, forecast bias, and risk-distribution health | features and prediction outputs | monitoring JSON and CSV evidence |
| `api.py` | serves health, readiness, model metadata, Prometheus-style metrics, and member-risk scoring | local joblib or MLflow model | versioned FastAPI contract |
| `quality.py` | provides reusable required-column, uniqueness, null-rate, and fail-fast quality checks | pandas DataFrames | structured quality results or publication failure |

## Business domains generated

The deterministic generator creates connected source data for:

```text
members
resorts
campaigns
reservations
resort stays
points transactions
vacation packages
tour events
sales contracts
marketing events
service cases
labor shifts
```

The relationships are intentionally nontrivial. Demand includes seasonality, holidays, and weekends. Marketing activity influences tour and contract behavior. Member engagement influences points activity and service friction. Labor demand is linked to resort arrivals.

## Declared grains

| Product | Grain |
|---|---|
| `dim_member` | one row per member |
| `dim_resort` | one row per resort |
| `dim_campaign` | one row per campaign |
| `fact_reservation` | one row per reservation |
| `fact_stay` | one row per stay |
| `fact_points_transaction` | one row per points transaction |
| `resort_monthly_performance` | resort + month |
| `campaign_tour_sales_attribution` | campaign + channel + market + month |
| `member_points_utilization` | member + month |
| `resort_labor_efficiency` | resort + business date |
| `member_month_features` | member + as-of month |
| `waterfall_resort_week_features` | resort + forecast week |

## Point-in-time feature correctness

### Member features

The member feature pipeline uses an explicit `2026-07-01` as-of date in the reference implementation. Every contributing event must occur before that cutoff.

Feature groups include:

- tenure, tier, and home market
- points earned, redeemed, expired, utilization, and expiration share
- stays, room nights, and revenue
- booking recency
- service cases, escalations, and average resolution duration

The generated future inactivity label is never included in `CHURN_NUMERIC` or `CHURN_CATEGORICAL`.

### Resort-week features

The forecasting feature pipeline creates a complete resort-week scaffold before generating:

- 1-, 4-, 13-, and 52-week arrival lags
- 4- and 13-week shifted rolling means
- calendar seasonality
- resort capacity and encoded resort identity
- market campaign intensity

Rolling values are shifted before aggregation so the target week cannot leak into its own predictors.

## Model validation

### Member risk

- stratified train/test split
- imputation, scaling, and one-hot encoding inside one scikit-learn pipeline
- class-balanced logistic regression
- ROC AUC, accuracy, precision, recall, F1, positive rate, and confusion matrix
- persisted probability and risk-band outputs

### Resort-week forecast

- chronological 80/20 split
- Random Forest regression reference model
- 52-week seasonal baseline
- MAE, WAPE, bias, test-row count, and cutoff evidence
- acceptance requires WAPE at or below `0.30` and no worse than the baseline

## Failure behavior

- Missing required columns, duplicate business keys, unacceptable null rates, or broken reservation foreign keys stop publication.
- Feature tests reject duplicate entity-time grains or missing lag values.
- Model acceptance tests fail the build when thresholds are missed.
- API readiness fails when the approved model cannot be loaded.
- Monitoring emits warning status when drift or forecast thresholds are exceeded.

## Local-to-managed mapping

| Local implementation | Databricks equivalent |
|---|---|
| CSV landing and Bronze files | cloud volume and Auto Loader Bronze tables |
| pandas conformance | Spark SQL/PySpark Silver processing |
| local Gold CSV and SQLite | Delta Gold tables and SQL warehouse consumption |
| pandas point-in-time features | Unity Catalog feature tables |
| joblib model artifact | MLflow registered model version |
| local acceptance tests | Databricks training gate and candidate evidence table |
| local score CSV | alias-based distributed batch score table |
| local API model | MLflow model URI or managed serving deployment |

## Run and verify

```bash
python scripts/run_all.py
pytest -q
```

Or execute the combined target:

```bash
make validate
```

Generated reviewer samples are published under [`../../examples/`](../../examples/README.md).
