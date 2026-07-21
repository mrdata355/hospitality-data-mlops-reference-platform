# Version 2: Governed Hospitality AI Operations

Version 2 extends the hospitality data and MLOps platform with an independently deployable AI operations control plane.

## What is implemented

- capability, cost, latency, and data-classification-aware provider routing
- deterministic primary-provider failure injection and approved fallback routing
- per-provider circuit breakers and per-workflow budget enforcement
- sensitive metadata redaction and prompt-injection blocking
- permissioned tools with explicit agent roles and action-risk levels
- Forecast Operations Analyst, Data Reliability Investigator, and Incident Commander agents
- tool-grounded incident findings, severity assignment, lineage evidence, and runbook selection
- mandatory human approval before model rollback
- immutable action and provider audit evidence
- FastAPI endpoints for incident analysis, report retrieval, provider status, tool catalog, and approval
- deterministic evaluation metrics and GitHub Actions acceptance gates

## Run

```bash
make ai-ops-test
make ai-ops-demo
make ai-ops-api
```

The API runs on port `8090`. Generated evidence is written to `artifacts/ai_ops/`.

## Architecture and controls

See [`docs/AI_OPERATIONS_CONTROL_PLANE.md`](docs/AI_OPERATIONS_CONTROL_PLANE.md).
