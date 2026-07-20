# Credential and Environment Setup

Credentials are intentionally absent. Add them only through approved secret stores.

## Local environment

Copy the template:

```bash
cp .env.example .env
```

The local deterministic path requires no cloud secrets.

## GitHub Actions secrets

For a future Databricks deployment workflow, create these repository secrets only when an approved workspace is available:

| Secret | Purpose |
|---|---|
| `DATABRICKS_HOST` | Workspace URL |
| `DATABRICKS_CLIENT_ID` | Service-principal or workload-identity client ID |
| `DATABRICKS_CLIENT_SECRET` | Client secret when federated identity is unavailable |
| `AZURE_TENANT_ID` | Azure tenant for workload identity |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription for approved infrastructure |
| `AZURE_CLIENT_ID` | Approved deployment identity |

Prefer workload identity or managed identity over long-lived client secrets.

## Kubernetes secrets

Do not place secrets in YAML committed to Git. Create them through the deployment platform or a secret manager. The API can use:

- `MODEL_SOURCE=local` for the generated local artifact
- `MODEL_SOURCE=mlflow` for an approved registry model
- `MODEL_URI` for the registered model alias or version

## Databricks local CLI

Use the Databricks CLI authentication flow or an approved profile. Never commit `~/.databrickscfg`.

## Pre-deployment checks

1. Confirm repository secret scanning is enabled.
2. Confirm `.env` and credential files are ignored.
3. Use separate dev, staging, and production identities.
4. Limit production writes to service principals.
5. Rotate any secret immediately if it is exposed.
