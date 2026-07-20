# System Validation Walkthrough

## Purpose

This walkthrough verifies the repository as an engineering system. It is intended for local development, code review, release validation, and architecture assessment. It does not require cloud credentials.

## 1. Build the local environment

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies and run the complete validation path:

```bash
pip install -r requirements.txt
make validate
```

The validation path performs the following operations:

```text
Generate deterministic source domains
  -> build Bronze ingestion outputs
  -> conform Silver entities
  -> build dimensions, facts, and Gold products
  -> build member-month and resort-week features
  -> train member-risk and forecast models
  -> evaluate model acceptance thresholds
  -> publish predictions and monitoring outputs
  -> export compact reviewer-safe examples
  -> execute automated tests
```

## 2. Verify generated evidence

Review the following outputs after validation:

| Evidence | Location |
|---|---|
| Source-domain row counts | `artifacts/run_summary.json` |
| Data-quality outcomes | `data/gold/data_quality_results.csv` |
| Member feature product | `data/gold/member_month_features.csv` |
| Resort-week feature product | `data/gold/waterfall_resort_week_features.csv` |
| Member-risk metrics | `artifacts/metrics/member_churn_metrics.json` |
| Forecast metrics | `artifacts/metrics/waterfall_forecast_metrics.json` |
| Forecast predictions | `artifacts/predictions/waterfall_forecast_resort_week.csv` |
| Drift and accuracy monitoring | `artifacts/monitoring/model_health.json` |
| Public-safe samples | `examples/` |

Acceptance criteria enforced by code and CI:

- member-risk ROC AUC must be at least `0.75`
- forecast WAPE must be at most `0.30`
- forecast WAPE must not exceed the 52-week seasonal baseline
- dimensional, feature, forecast, and sample grains must remain unique
- committed examples must match regenerated pipeline outputs

## 3. Validate the scoring API

Start the service:

```bash
make api
```

Service endpoints:

```text
GET  /health
GET  /ready
GET  /model-info
GET  /metrics
POST /score/member-churn
```

Example request:

```bash
curl -X POST http://localhost:8080/score/member-churn \
  -H "Content-Type: application/json" \
  -H "x-request-id: validation-001" \
  -d '{
    "tenure_months": 36,
    "points_earned_12m": 28000,
    "points_redeemed_12m": 8000,
    "points_expired_12m": 2500,
    "points_utilization_rate": 0.2857,
    "expired_share": 0.089,
    "stays_12m": 1,
    "room_nights_12m": 4,
    "net_room_revenue_12m": 1250,
    "service_cases_90d": 2,
    "escalated_cases_90d": 1,
    "avg_resolution_hours_90d": 52,
    "days_since_last_booking": 230,
    "member_tier": "Member",
    "home_market": "Orlando"
  }'
```

Verify that the response contains:

- a probability between `0` and `1`
- a valid risk band
- the active model alias
- a score timestamp
- a request identifier matching the response header

## 4. Validate the container path

Generate the local model artifact before building the image:

```bash
python scripts/run_all.py
docker compose up --build
```

Confirm that Docker health checks use `/ready` and that the container runs as a non-root user.

## 5. Exercise representative API load

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Start the service, then run Locust:

```bash
make api
make loadtest
```

The load profile exercises scoring, readiness, and liveness endpoints while validating response contracts. Results from a controlled environment should be retained before making throughput or latency claims.

## 6. Inspect managed-platform definitions

The credential-free local path validates business logic and release controls. The managed Databricks path is defined under:

- `sql/databricks/`
- `databricks/databricks.yml`
- `databricks/resources/jobs.yml`
- `databricks/resources/rollback.yml`
- `databricks/src_databricks/`

The workflow order is:

```text
build member features
build resort-week features
train forecast candidate
validate absolute and baseline thresholds
register immutable model version
promote approved alias
batch score
monitor
```

A live deployment additionally requires authorized workspace access, identities, Unity Catalog permissions, source volumes, networking, secrets, policies, and operational approval.

## 7. Failure and recovery checks

Use the documentation and code to confirm these safeguards:

- a failed data-quality gate stops dependent publication
- a rejected model candidate does not move the active alias
- the previous model version remains available for rollback
- readiness prevents traffic from reaching an unloaded model
- the prior successful serving state is preserved when a new run fails
- immutable generated inputs permit deterministic replay
