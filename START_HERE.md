# Local Validation and Deployment Guide

This guide describes how to run, verify, and inspect the platform without cloud credentials.

## System scope

The repository implements a hospitality data and MLOps reference platform with:

- deterministic synthetic source generation
- Bronze, Silver, conformed dimensional, and Gold processing
- point-in-time member and resort-week feature products
- member-risk classification and resort-week forecasting
- model acceptance gates and seasonal-baseline comparison
- FastAPI scoring, Docker, Kubernetes, and health/readiness probes
- Databricks Asset Bundles, MLflow promotion, rollback, monitoring, SLOs, and runbooks

The repository contains no real customer records, production credentials, proprietary source-system details, or deployed company infrastructure.

## Local environment

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

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

Expected validation outcomes:

- the automated test suite passes
- member-risk ROC AUC remains at or above `0.75`
- forecast WAPE remains at or below `0.30`
- forecast WAPE remains no worse than the 52-week seasonal baseline
- generated datasets, features, models, metrics, predictions, examples, and monitoring outputs are recreated from source

## API execution

Start the scoring API:

```bash
make api
```

Available endpoints:

- `http://localhost:8080/docs`
- `http://localhost:8080/health`
- `http://localhost:8080/ready`
- `http://localhost:8080/model-info`
- `http://localhost:8080/metrics`

## Container execution

Generate the local model artifact before building the image:

```bash
python scripts/run_all.py
docker compose up --build
```

The container runs as a non-root user and uses the readiness endpoint for its health check.

## Load validation

Install development dependencies, start the API, and launch Locust:

```bash
pip install -r requirements-dev.txt
make api
make loadtest
```

The load profile exercises scoring, readiness, and liveness endpoints with generated feature payloads. Retain controlled test results before making capacity or latency claims.

## Credential management

Never commit passwords, access tokens, client secrets, private keys, `.env`, Databricks profiles, kubeconfigs, or cloud credential files.

Use `.env.example` only as a template. Approved GitHub Actions secrets belong under:

`Repository Settings → Secrets and variables → Actions`

See `docs/CREDENTIAL_SETUP.md` for environment placeholders and identity guidance.

## Databricks deployment path

Install the Databricks CLI, authenticate with an approved identity, and validate the development target:

```bash
cd databricks
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run hospitality_data_platform_pipeline -t dev
```

Do not run staging or production targets until workspace identities, catalog permissions, cluster policies, source volumes, network controls, secrets, and approvals are configured.

## Recommended inspection order

1. `README.md` for scope and verified evidence
2. `examples/` for generated inputs and outputs
3. `src/hospitality_data_platform/` for the local implementation
4. `sql/databricks/` for Spark SQL and lakehouse assets
5. `databricks/` for managed workflows, MLflow lifecycle, scoring, and rollback
6. `tests/` and `.github/workflows/ci.yml` for validation controls
7. `k8s/` for serving availability, scaling, and security controls
8. `docs/` for architecture, contracts, SLOs, operations, and production boundaries

## Core validation references

- `docs/SYSTEM_VALIDATION_WALKTHROUGH.md`
- `docs/CAPABILITY_MATRIX.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_CONTRACTS.md`
- `docs/PRODUCTION_SYSTEM_DESIGN.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/PRODUCTION_READINESS.md`
