# Model Governance

## Required model evidence

Every candidate model records:

- business owner and technical owner
- prediction target and grain
- training and validation windows
- feature contract version
- source-code commit
- parameters and environment
- primary and guardrail metrics
- baseline comparison
- threshold decision
- fairness and sensitive-feature review
- intended use and prohibited use
- rollback target

## Promotion policy

A training run may register a candidate, but it cannot change the production alias unless all acceptance gates pass. Promotion requires metric evidence, contract compatibility, representative scoring, rollback readiness, and an authorized release decision.

## Monitoring policy

Monitor input drift, missingness, feature freshness, prediction distribution, model accuracy after labels mature, business intervention rates, latency, errors, and cost. Alerts must identify whether the problem is data, model, code, infrastructure, or business-process related.

## Retirement policy

A model is retired when its business use ends, a replacement is fully promoted, required data is no longer lawful or available, or operational risk exceeds value. Artifacts and audit evidence follow the approved retention policy.
