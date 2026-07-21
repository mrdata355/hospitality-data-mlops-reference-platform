# Two-Minute Executive Demonstration

This demonstration presents the platform as an operating system with measurable controls rather than as a collection of source files. It uses generated non-production data only.

## Local one-command demonstration

Prerequisites:

- Python 3.11 with the exact repository dependencies installed
- Docker with Docker Compose

Run:

```bash
make executive-demo
```

The command performs the following sequence:

1. regenerates all deterministic source domains and data products
2. trains the member-risk and resort-week forecasting models
3. applies model acceptance gates
4. executes the expanding-window rolling-origin backtest
5. builds and starts the API container with the repository security restrictions
6. verifies readiness, version metadata, model metadata, scoring, request IDs, and metrics
7. writes `artifacts/demo/executive_demo.json`
8. stops the local container after validation

Use the faster mode only after the data, models, and backtest evidence already exist:

```bash
python scripts/run_local_executive_demo.py --skip-pipeline
```

## Narration

### 0:00 to 0:20 — Business problem

> Hospitality data is normally split across reservations, members, points, tours, contracts, marketing, service, labor, and resort operations. This platform gives those domains stable contracts and grains so analytics and machine learning use the same governed foundation.

Show the architecture diagram near the top of `README.md`.

### 0:20 to 0:45 — Governed data foundation

> The pipeline generates twelve connected operational domains, applies Bronze lineage, Silver conformance and quality controls, then publishes conformed dimensions, atomic facts, Gold products, and point-in-time feature tables. Grain and foreign-key failures stop publication.

Show the terminal line reporting the source-domain, reservation, and labor-shift counts.

### 0:45 to 1:15 — Model validation

> The member-risk model must clear a ROC AUC threshold. The resort-week forecast must pass an absolute WAPE gate and beat a seasonal baseline. Forecast robustness is also checked through expanding-window rolling-origin folds with strict temporal separation.

Show the model and rolling-origin lines from the executive-demo output.

### 1:15 to 1:40 — Serving and software assurance

> A validated model artifact is handed to a separate serving build. The container runs as a fixed non-root user with a read-only filesystem, dropped capabilities, no privilege escalation, health checks, immutable build metadata, API contract validation, metrics, and concurrent performance testing.

Open `/version`, `/model-info`, or `/metrics`, then show the sample score from the terminal.

### 1:40 to 2:00 — Operational judgment and boundary

> The repository includes promotion, monitoring, rollback, incident-response, Kubernetes, and Azure deployment controls. The local path and container validation are executable. Cloud definitions are not described as a company deployment until a sanitized cloud run has produced evidence.

End on `docs/EXECUTIVE_OVERVIEW.md` or the generated executive-demo JSON.

## Validate an existing endpoint

The same demonstration command works against a deployed service:

```bash
python scripts/run_executive_demo.py \
  --base-url https://YOUR_APP_FQDN \
  --evidence artifacts/deployment/executive-demo.json
```

The endpoint must pass health, readiness, version, model-contract, score, request-ID, and metrics checks before the report is marked `PASS`.

## Azure Container Apps deployment

The manual workflow `.github/workflows/deploy-azure-demo.yml` builds the deterministic model artifact, builds the container in Azure Container Registry, deploys a public Azure Container App, validates the live endpoint, and uploads sanitized evidence.

### One-time GitHub environment setup

Create a GitHub environment named `azure-demo` and add these environment secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

The identity must have an OpenID Connect federated credential for this repository and sufficient access to create the dedicated resource group, registry, role assignment, Container Apps environment, and Container App.

Microsoft setup reference:

- <https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect>

### Run the deployment

1. Open **Actions**.
2. Select **deploy-azure-demo**.
3. Select **Run workflow**.
4. Enter a globally unique lowercase Azure Container Registry name.
5. Keep the resources in a dedicated demo resource group.

The workflow publishes the live URL in the run summary and stores:

```text
artifacts/deployment/azure-container-app.json
artifacts/deployment/executive-demo.json
```

### Remove demo resources

Delete only the dedicated demo resource group:

```bash
az group delete \
  --name hospitality-data-mlops-demo-rg \
  --yes \
  --no-wait
```

Do not use that cleanup command for a resource group containing unrelated resources.

## Evidence boundary

A successful local run proves the credential-free platform, model gates, temporal validation, secured container path, and API contract. A successful Azure workflow run additionally proves that the sanitized image was built, deployed, reached through public ingress, and validated at the recorded commit.

Neither result is a claim of real-customer predictive lift, company adoption, production authorization, or enterprise-scale workload execution.
