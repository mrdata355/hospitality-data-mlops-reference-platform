# Automated Validation and Acceptance Gates

The test suite validates data-engineering correctness, point-in-time feature behavior, model acceptance, API contracts, reviewer evidence, Databricks workflow controls, environment isolation, and rollback readiness.

GitHub Actions regenerates all synthetic inputs, artifacts, and reviewer samples before running the tests. This prevents committed outputs from masking pipeline failures.

## Test matrix

| Test file | Controls validated |
|---|---|
| `test_pipeline.py` | dimension and business-key uniqueness, fact foreign keys, Gold product grains |
| `test_features_and_models.py` | member feature grain, target leakage exclusion, lag completeness, model acceptance thresholds |
| `test_api.py` | health, readiness, model metadata, Prometheus-style metrics, scoring contract, payload validation, request IDs |
| `test_examples.py` | sample-file presence, compact row limits, public-safe schemas, feature and forecast grains, quality status, validation summary |
| `test_production_assets.py` | independent-use disclaimer, environment catalog isolation, workflow dependency order, promotion before scoring, runtime catalog configuration, SQL parameterization, acceptance gates, local/MLflow model sources, rollback workflow |

## Acceptance thresholds

The credential-free CI path enforces:

```text
member-risk ROC AUC >= 0.75
forecast WAPE <= 0.30
forecast WAPE <= seasonal baseline WAPE
all committed sample data-quality checks = PASS
member features are unique by member_id + as_of_month
forecast samples are unique by resort_id + forecast_week_start + forecast_run_id
```

## Test categories

### Data contracts and grains

- required columns exist
- business keys are unique
- reservation member and resort foreign keys resolve
- conformed dimensions remain unique by surrogate and business key
- Gold marts remain unique at their declared grains

### Point-in-time features

- member features remain one row per member and cutoff month
- the generated label is not part of the model feature lists
- resort-week lags and rolling features have no missing values after the eligibility window
- time-aware feature logic excludes target-period information

### Model validation

- the member-risk model clears the minimum ROC AUC threshold
- the resort-week model clears the absolute WAPE gate
- the resort-week model performs no worse than the 52-week seasonal baseline
- expected model and monitoring evidence files are generated

### API behavior

- `/health` confirms the process is alive
- `/ready` confirms the model is loaded and traffic can be accepted
- `/model-info` exposes controlled model and feature metadata
- `/metrics` publishes request, error, and latency counters
- `/score/member-churn` validates input constraints and returns probability, risk band, alias, timestamp, and request ID

### Managed deployment assets

Static tests verify that:

- development, staging, and production use isolated catalogs
- Waterfall features are built before training
- model promotion occurs before batch scoring
- rejected candidates raise a failed task
- SQL assets use runtime catalog parameters
- batch and API serving can use an approved model alias
- rollback restores a recorded prior version

## Run locally

The pipeline must create the generated inputs and artifacts before tests execute:

```bash
python scripts/run_all.py
python scripts/export_examples.py
pytest -q
```

Or run the combined command:

```bash
make validate
```

## CI order

```text
install dependencies
→ compile Python assets
→ run deterministic pipeline
→ regenerate reviewer samples
→ verify no sample drift
→ execute pytest
→ enforce model acceptance gates
→ verify release assets
```

## What the tests do not claim

Passing these tests demonstrates reproducible implementation behavior and production-style controls. It does not by itself prove live Azure capacity, Databricks workspace permissions, production source quality, real customer outcomes, or enterprise load limits. Those require an authorized deployment and measured operational evidence.
