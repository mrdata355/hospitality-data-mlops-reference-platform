## Purpose

Describe the business, data, model, or platform outcome and why the change is needed.

## Scope

Summarize the implementation and identify affected schemas, grains, interfaces, workflows, models, or deployment assets.

## Validation

- [ ] `make validate`
- [ ] `make quality`
- [ ] `make security`
- [ ] Rolling-origin backtesting completed when forecast or feature logic changed
- [ ] Container smoke test and benchmark completed when serving behavior changed
- [ ] Data-contract, schema, grain, and lineage impact reviewed
- [ ] Model-metric impact reviewed when applicable
- [ ] Security and privacy impact reviewed
- [ ] Documentation and machine-readable evidence updated

## Operational impact

Document runtime, cost, SLO, observability, backfill, migration, deployment, and rollback implications.

## Evidence boundary

Confirm that no credentials, production records, confidential mappings, or unsupported deployment claims were introduced. Distinguish executable local controls from managed-environment reference definitions when applicable.
