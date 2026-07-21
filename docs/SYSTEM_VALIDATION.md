# System Validation

This document defines the repeatable validation path for the generated-data platform.

## Local validation

Prerequisites:

- Python 3.11 with the exact repository dependencies installed
- Docker with Docker Compose

Run:

```bash
make system-validation
```

The command:

1. regenerates the deterministic source domains and data products
2. trains the member-risk and resort-week forecasting models
3. applies model acceptance gates
4. executes the expanding-window rolling-origin backtest
5. builds and starts the API container with the repository security restrictions
6. verifies readiness, version metadata, model metadata, scoring, request IDs, and metrics
7. writes `artifacts/validation/system_validation.json`
8. stops the local container after validation

The shorter mode can be used when the data, models, and backtest evidence already exist:

```bash
python scripts/run_local_system_validation.py --skip-pipeline
```

## Validate an existing endpoint

```bash
python scripts/run_system_validation.py \
  --base-url https://YOUR_APP_FQDN \
  --evidence artifacts/deployment/system-validation.json
```

The endpoint must pass health, readiness, version, model-contract, score, request-ID, and metrics checks before the report is marked `PASS`.

## Azure Container Apps validation

The manual workflow `.github/workflows/deploy-azure-validation.yml` builds the deterministic model artifact, builds the container in Azure Container Registry, deploys an Azure Container App, validates the endpoint, and uploads sanitized evidence.

### GitHub environment

Create a GitHub environment named `azure-validation` with these environment secrets:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

The identity must have an OpenID Connect federated credential for this repository and sufficient access to create the dedicated resource group, registry, role assignment, Container Apps environment, and Container App.

Microsoft setup reference:

- <https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect>

### Deployment execution

The workflow requires:

- an Azure region
- a resource group dedicated to validation resources
- a Container Apps environment name
- a Container App name
- a globally unique lowercase Azure Container Registry name

The workflow stores:

```text
artifacts/deployment/azure-container-app.json
artifacts/deployment/system-validation.json
```

### Resource cleanup

Delete only the dedicated validation resource group:

```bash
az group delete \
  --name hospitality-data-mlops-validation-rg \
  --yes \
  --no-wait
```

Do not use that command for a resource group containing unrelated resources.

## Evidence boundary

A successful local run validates the credential-free platform, model gates, temporal evaluation, secured container path, and API contract. A successful Azure workflow run additionally validates that the generated-data image was built, deployed, reached through public ingress, and checked at the recorded commit.

These results are not claims of real-customer predictive lift, company adoption, production authorization, or enterprise-scale workload execution.
