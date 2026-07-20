# Production Readiness Checklist

This checklist separates evidence verified in the independent reference implementation from controls that require an authorized deployment environment.

## Verified in this package

- [x] Generated source contracts, business keys, grains, event fields, and update semantics are documented.
- [x] Local replay-oriented Bronze metadata, Silver conformance, dimensional grains, and quality outputs execute deterministically.
- [x] Point-in-time feature logic and chronological forecast validation are tested.
- [x] Forecast acceptance requires an absolute threshold and seasonal-baseline improvement.
- [x] Databricks dev, staging, and production catalogs are isolated and passed to workloads at runtime.
- [x] The Databricks workflow builds forecast features before training and promotes an alias only after acceptance.
- [x] A separate rollback workflow restores the latest recorded prior model version.
- [x] Docker, Kubernetes probes, resources, non-root controls, rolling deployment, and autoscaling definitions are included.
- [x] CI runs the deterministic pipeline, tests, acceptance gates, Python compilation, and production-asset validation.
- [x] SLOs, incident severity, operations, security, cost, and rollback procedures are documented.

## Required before an authorized production deployment

- [ ] Authorized customer source owners approve contracts and source-to-target mappings.
- [ ] Live source delivery, late-arriving behavior, replay, quarantine, and correction procedures are tested in the target workspace.
- [ ] Unity Catalog groups, service principals, managed identities, secrets, cluster policies, and network controls are provisioned.
- [ ] Data-retention, deletion, PII, lineage, and audit requirements are approved by governance and security teams.
- [ ] Model labels, thresholds, fairness considerations, business interventions, and acceptance criteria are approved by accountable owners.
- [ ] Staging smoke, schema, shadow, load, recovery, and rollback tests pass with production-like data volumes.
- [ ] Alert destinations, on-call ownership, incident contacts, SLO measurement, and escalation paths are active.
- [ ] Production cost budget, endpoint limits, auto-termination, storage lifecycle, and retry controls are approved.
- [ ] Release owner, change record, rollback version, deployment window, and business sign-off are recorded.
