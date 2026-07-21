#!/usr/bin/env bash
set -Eeuo pipefail

: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID.}"
: "${ACR_NAME:?Set a globally unique lowercase ACR_NAME.}"

LOCATION="${LOCATION:-eastus}"
RESOURCE_GROUP="${RESOURCE_GROUP:-hospitality-data-mlops-validation-rg}"
CONTAINER_APP_ENVIRONMENT="${CONTAINER_APP_ENVIRONMENT:-hospitality-validation-env}"
CONTAINER_APP_NAME="${CONTAINER_APP_NAME:-hospitality-member-risk-validation}"
IMAGE_NAME="${IMAGE_NAME:-member-risk-api}"
SERVICE_VERSION="${SERVICE_VERSION:-1.1.0}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short=12 HEAD)}"
BUILD_SHA="${BUILD_SHA:-$(git rev-parse HEAD)}"
BUILD_DATE="${BUILD_DATE:-$(date -u +'%Y-%m-%dT%H:%M:%SZ')}"
DEPLOYMENT_EVIDENCE="${DEPLOYMENT_EVIDENCE:-artifacts/deployment/azure-container-app.json}"

for command in az git python; do
  if ! command -v "${command}" >/dev/null 2>&1; then
    echo "Required command is unavailable: ${command}" >&2
    exit 1
  fi
done

if [[ ! -f artifacts/models/member_churn_model.joblib ]]; then
  echo "Model artifact is missing. Building deterministic platform artifacts."
  python scripts/run_all.py
fi

az account set --subscription "${AZURE_SUBSCRIPTION_ID}"
az extension add --name containerapp --upgrade --yes >/dev/null
az provider register --namespace Microsoft.App --wait >/dev/null
az provider register --namespace Microsoft.OperationalInsights --wait >/dev/null

az group create \
  --name "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --tags workload=hospitality-reference purpose=system-validation data=synthetic \
  >/dev/null

if ! az acr show --name "${ACR_NAME}" --resource-group "${RESOURCE_GROUP}" >/dev/null 2>&1; then
  az acr create \
    --name "${ACR_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --location "${LOCATION}" \
    --sku Basic \
    --admin-enabled false \
    >/dev/null
fi

az acr build \
  --registry "${ACR_NAME}" \
  --image "${IMAGE_NAME}:${IMAGE_TAG}" \
  --build-arg "SERVICE_VERSION=${SERVICE_VERSION}" \
  --build-arg "VCS_REF=${BUILD_SHA}" \
  --build-arg "BUILD_DATE=${BUILD_DATE}" \
  .

if ! az containerapp env show \
  --name "${CONTAINER_APP_ENVIRONMENT}" \
  --resource-group "${RESOURCE_GROUP}" \
  >/dev/null 2>&1; then
  az containerapp env create \
    --name "${CONTAINER_APP_ENVIRONMENT}" \
    --resource-group "${RESOURCE_GROUP}" \
    --location "${LOCATION}" \
    >/dev/null
fi

if ! az containerapp show \
  --name "${CONTAINER_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  >/dev/null 2>&1; then
  az containerapp create \
    --name "${CONTAINER_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --environment "${CONTAINER_APP_ENVIRONMENT}" \
    --image mcr.microsoft.com/k8se/quickstart:latest \
    --ingress external \
    --target-port 80 \
    --min-replicas 0 \
    --max-replicas 2 \
    --tags workload=hospitality-reference purpose=system-validation data=synthetic \
    >/dev/null
fi

az containerapp identity assign \
  --name "${CONTAINER_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --system-assigned \
  >/dev/null

PRINCIPAL_ID="$(az containerapp identity show \
  --name "${CONTAINER_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query principalId \
  --output tsv)"
ACR_ID="$(az acr show \
  --name "${ACR_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query id \
  --output tsv)"

ROLE_COUNT="$(az role assignment list \
  --assignee "${PRINCIPAL_ID}" \
  --scope "${ACR_ID}" \
  --role AcrPull \
  --query 'length(@)' \
  --output tsv)"
if [[ "${ROLE_COUNT}" == "0" ]]; then
  az role assignment create \
    --assignee-object-id "${PRINCIPAL_ID}" \
    --assignee-principal-type ServicePrincipal \
    --role AcrPull \
    --scope "${ACR_ID}" \
    >/dev/null
fi

az containerapp registry set \
  --name "${CONTAINER_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --server "${ACR_NAME}.azurecr.io" \
  --identity system \
  >/dev/null

az containerapp ingress update \
  --name "${CONTAINER_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --type external \
  --target-port 8080 \
  --transport auto \
  --allow-insecure false \
  >/dev/null

IMAGE="${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"
updated=false
for attempt in $(seq 1 8); do
  if az containerapp update \
    --name "${CONTAINER_APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --image "${IMAGE}" \
    --cpu 0.5 \
    --memory 1.0Gi \
    --min-replicas 0 \
    --max-replicas 2 \
    --set-env-vars \
      APP_ENV=azure-validation \
      MODEL_SOURCE=local \
      MODEL_ALIAS=Champion \
      SERVICE_VERSION="${SERVICE_VERSION}" \
      BUILD_SHA="${BUILD_SHA}" \
    >/dev/null; then
    updated=true
    break
  fi
  echo "Image update attempt ${attempt} failed; waiting for role propagation." >&2
  sleep 20
done

if [[ "${updated}" != "true" ]]; then
  echo "Container App image update failed after role-propagation retries." >&2
  exit 1
fi

FQDN="$(az containerapp show \
  --name "${CONTAINER_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query properties.configuration.ingress.fqdn \
  --output tsv)"

mkdir -p "$(dirname "${DEPLOYMENT_EVIDENCE}")"
python - \
  "${DEPLOYMENT_EVIDENCE}" \
  "${AZURE_SUBSCRIPTION_ID}" \
  "${RESOURCE_GROUP}" \
  "${LOCATION}" \
  "${CONTAINER_APP_ENVIRONMENT}" \
  "${CONTAINER_APP_NAME}" \
  "${ACR_NAME}" \
  "${IMAGE}" \
  "${FQDN}" \
  "${BUILD_SHA}" \
  "${SERVICE_VERSION}" <<'PY'
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    evidence_path,
    subscription_id,
    resource_group,
    location,
    environment,
    app_name,
    registry,
    image,
    fqdn,
    build_sha,
    service_version,
) = sys.argv[1:]

payload = {
    "status": "DEPLOYED_PENDING_APPLICATION_VALIDATION",
    "deployed_at": datetime.now(timezone.utc).isoformat(),
    "subscription_id_suffix": subscription_id[-6:],
    "resource_group": resource_group,
    "location": location,
    "container_app_environment": environment,
    "container_app_name": app_name,
    "registry": registry,
    "image": image,
    "url": f"https://{fqdn}",
    "build_sha": build_sha,
    "service_version": service_version,
    "data_boundary": "generated non-production data only",
}
Path(evidence_path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
PY

echo "Azure Container App deployed: https://${FQDN}"
echo "Deployment evidence: ${DEPLOYMENT_EVIDENCE}"
