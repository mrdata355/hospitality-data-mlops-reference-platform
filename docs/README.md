# Architecture and Operating Documentation

This directory contains the system design, validation procedures, capability index, data contracts, data dictionary, deployment model, service objectives, security controls, cost controls, incident response, production-readiness checklist, and architecture decision records.

## Core references

| Document | Purpose |
|---|---|
| `SYSTEM_VALIDATION_WALKTHROUGH.md` | Reproduce and inspect the full credential-free system |
| `CAPABILITY_MATRIX.md` | Map platform capabilities to implementation evidence |
| `ARCHITECTURE.md` | Describe logical layers, data flow, grains, and failure boundaries |
| `PRODUCTION_SYSTEM_DESIGN.md` | Capture system-level design decisions and recovery behavior |
| `DATA_CONTRACTS.md` | Define source, feature, quality, and change contracts |
| `DATA_DICTIONARY.md` | Document important dimensions, facts, and feature fields |
| `DEPLOYMENT.md` | Define release, Databricks, container, and Kubernetes deployment paths |
| `SLO_SLA.md` | Define freshness, availability, quality, model, and latency objectives |
| `OPERATIONS_RUNBOOK.md` | Provide replay, rollback, quality-failure, and service-recovery procedures |
| `SECURITY_GOVERNANCE.md` | Define access, sensitive-data, identity, and audit controls |
| `PRODUCTION_READINESS.md` | Separate verified repository evidence from environment-dependent requirements |

The documentation distinguishes locally verified behavior from cloud deployment requirements that depend on authorized infrastructure, identities, networking, source contracts, and operational approval.
