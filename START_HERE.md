# Start Here: Kellon Lewis Portfolio Runbook

This guide walks through the repository in the same order used to validate it.

## 1. What this repository proves

The project is an independent, production-style hospitality data and MLOps reference implementation. It demonstrates:

- deterministic synthetic source generation
- Bronze, Silver, conformed dimensional, and Gold processing
- point-in-time feature engineering
- member-risk classification and resort-week forecasting
- model acceptance gates and seasonal-baseline comparison
- FastAPI scoring, Docker, Kubernetes, and health/readiness probes
- Databricks Asset Bundles, MLflow promotion, rollback, monitoring, SLOs, and runbooks

It contains no real customer records, credentials, proprietary source-system details, or deployed company infrastructure.

## 2. First local run

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

Install and verify:

```bash
pip install -r requirements.txt
python scripts/run_all.py
pytest -q
```

Expected verification evidence:

- 20 passing tests
- member-risk ROC AUC at or above 0.75
- forecast WAPE at or below 0.30
- forecast WAPE no worse than the 52-week seasonal baseline

## 3. Run the API

```bash
make api
```

Open:

- `http://localhost:8080/docs`
- `http://localhost:8080/health`
- `http://localhost:8080/ready`
- `http://localhost:8080/model-info`

## 4. Run with Docker

The model must be generated once before building the local image:

```bash
python scripts/run_all.py
docker compose up --build
```

## 5. Add credentials later

Never commit passwords, access tokens, client secrets, private keys, `.env`, Databricks profiles, or cloud credential files.

Use `.env.example` only as a template. For GitHub Actions or cloud deployment, add secrets in GitHub under:

`Repository Settings → Secrets and variables → Actions`

See `docs/CREDENTIAL_SETUP.md` for the exact placeholders.

## 6. Databricks path

Install the Databricks CLI, authenticate locally, then validate the development bundle:

```bash
cd databricks
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run hospitality_data_platform_pipeline -t dev
```

Do not run staging or production targets until workspace identities, catalog permissions, cluster policies, source volumes, and approvals are configured.

## 7. How to explain the project

Use this sequence in a technical walkthrough:

1. Business problem and platform boundaries
2. Source generation and replayable Bronze
3. Silver quality controls and declared grain
4. Gold analytical products
5. Point-in-time features and leakage prevention
6. Model validation and baseline gates
7. Registry promotion and rollback
8. API/Kubernetes serving
9. CI/CD, SLOs, security, incident response, and cost controls

## 8. Important evidence files

- `README.md`
- `docs/EXECUTIVE_OVERVIEW.md`
- `docs/IMPLEMENTATION_EVIDENCE.md`
- `docs/PRODUCTION_SYSTEM_DESIGN.md`
- `.github/workflows/ci.yml`
- `tests/`
- `databricks/`
- `k8s/`
