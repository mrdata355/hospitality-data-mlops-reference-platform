# Technical Interview Demonstration

## Objective

Demonstrate a complete feature engineering and MLOps workflow in 10 to 15 minutes without cloud credentials.

## Before the interview

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
make validate
```

Start the service in a second terminal:

```bash
make api
```

Open these pages before screen sharing:

- repository root
- GitHub Actions workflow
- `http://localhost:8080/docs`
- `http://localhost:8080/model-info`
- `http://localhost:8080/metrics`

## Demonstration sequence

### Minute 0–1: Business problem

Say:

> The repository solves two connected problems: reusable feature delivery and reliable model operations. The lakehouse standardizes the raw data, point-in-time feature products support training and inference, and the MLOps control plane manages acceptance, promotion, scoring, monitoring, and rollback.

Show:

- root `README.md`
- `PROJECTS.md`
- architecture diagram in `docs/TECHNICAL_SHOWCASE.md`

### Minute 1–3: Lakehouse and data modeling

Show:

- `src/hospitality_data_platform/pipeline_ingestion.py`
- `src/hospitality_data_platform/pipeline_dimensional.py`
- `sql/databricks/03_dimensional_model.sql`

Explain:

- Bronze retains ingestion metadata and replay evidence.
- Silver normalizes records and enforces keys.
- Facts declare atomic grain before aggregation.
- Dimensions standardize member, resort, campaign, and date context.

Principal-level point:

> I prevent metric inflation by establishing each business grain before joining or aggregating. The same conformed facts support ML features and analytical products.

### Minute 3–5: Reusable point-in-time features

Show:

- `src/hospitality_data_platform/features.py`
- `sql/databricks/05_feature_store.sql`
- `docs/DATA_CONTRACTS.md`

Explain:

- member-month and resort-week grains
- event-time cutoffs
- lag and rolling features
- training/inference feature consistency
- label excluded from model feature lists

Principal-level point:

> A Feature Store is not just a table registry. It needs entity keys, as-of semantics, quality gates, lineage, ownership, and consistent retrieval for both historical training and current inference.

### Minute 5–7: Waterfall forecasting lifecycle

Show:

- `databricks/src_databricks/build_waterfall_features.py`
- `databricks/src_databricks/train_waterfall.py`
- `databricks/src_databricks/promote_waterfall.py`
- `databricks/resources/jobs.yml`

Explain:

- chronological split
- 52-week seasonal baseline
- WAPE acceptance threshold
- immutable registered candidate
- alias promotion only after acceptance
- previous alias version retained for rollback

Principal-level point:

> Training success does not equal deployment approval. The active model changes only when objective quality gates pass, and a rejected candidate cannot disrupt the current Champion.

### Minute 7–9: API and Kubernetes

Show:

- FastAPI Swagger page
- `/model-info`
- `/metrics`
- `k8s/deployment.yaml`
- `k8s/hpa.yaml`
- `k8s/pdb.yaml`

Explain:

- Pydantic input contract
- request correlation ID
- separate liveness and readiness
- non-root container
- rolling update with zero planned unavailability
- horizontal scaling and disruption protection

Principal-level point:

> Readiness protects traffic from an unloaded or unavailable model, while liveness determines whether the process should be restarted. Those are different failure modes and should not share one probe.

### Minute 9–11: CI/CD and monitoring

Show:

- `.github/workflows/ci.yml`
- `src/hospitality_data_platform/monitoring.py`
- `docs/SLO_SLA.md`
- `docs/OPERATIONS_RUNBOOK.md`

Explain:

- CI regenerates the system from source
- tests validate grains and model gates
- monitoring tracks drift, WAPE, bias, score distribution, latency, and errors
- runbook defines replay and rollback

Principal-level point:

> I treat data, features, models, and serving infrastructure as one release system. A model should not be promoted when its feature contract, quality evidence, or rollback path is incomplete.

### Minute 11–12: Honest boundary

Say:

> The credential-free local path is working and CI validated. The Azure, Databricks, Unity Catalog, MLflow, and Kubernetes assets are deployment-ready reference definitions. I would validate them in an authorized environment with real identities, policies, networking, source contracts, load tests, and operational sign-off before describing the system as a live production deployment.

## Commands to demonstrate

### Full validation

```bash
make validate
```

### Example score request

```bash
curl -X POST http://localhost:8080/score/member-churn \
  -H "Content-Type: application/json" \
  -H "x-request-id: interview-demo-001" \
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

### Load test

```bash
pip install -r requirements-dev.txt
make loadtest
```

## Questions to expect

### How do you prevent feature leakage?

Features use an explicit as-of date. Event filters end before that date, labels are calculated separately, lag windows shift before rolling aggregation, and tests ensure the label is not included in the model feature list.

### How do you guarantee training and inference consistency?

The model uses explicit shared feature lists and input types. Historical and current features follow the same contract and cutoff logic. The API validates the inference payload, and the managed path adds MLflow signatures and a registered model alias.

### What happens when a new model performs worse?

The acceptance task fails. The candidate may remain as evidence, but the `Champion` alias is not changed. Existing batch and online consumers continue using the approved version.

### How would this scale to billions of records?

Move execution from pandas to the included Spark/Databricks path, process incrementally, partition or cluster by high-value access patterns, compact Delta files, isolate workloads, use Photon-capable job clusters when approved, avoid full-table rewrites, materialize stable feature products, and apply workload-specific autoscaling and cost controls.

### Why use both batch and real-time scoring?

Forecasting and broad member refreshes are naturally batch-oriented and benefit from replay and auditability. Real-time scoring is reserved for interactions where synchronous decisions justify the additional availability and cost requirements.

### What would you add in the authorized environment?

- real source contracts and incremental ingestion schedules
- Unity Catalog grants and lineage verification
- Key Vault and workload identity
- production cluster policies
- Terraform or Bicep for approved infrastructure
- Azure Monitor, Prometheus, and Grafana integrations
- load, failover, backup, restore, and disaster-recovery evidence
- business-approved model thresholds and alert routes
