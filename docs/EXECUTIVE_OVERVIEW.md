# Executive Overview

## Hospitality Data and MLOps Reference Platform

**Designed and implemented by Kellon Lewis**

This independent reference implementation demonstrates a governed, production-style operating model for hospitality and vacation-ownership data. It uses generated non-production records and does not represent an approved or deployed production system for any real hospitality company.

## What it proves

The repository is not limited to a notebook or isolated model. It implements the complete path from generated source records through Bronze and Silver processing, dimensional facts and dimensions, Gold business products, point-in-time features, model training, objective acceptance gates, registered-model promotion, scoring, API contracts, observability, rollback, security controls, cost controls, and incident response.

## Verified results

| Evidence | Result |
|---|---:|
| Automated validation | See current `pytest -q` result and CI workflow |
| Member-risk ROC AUC | 0.811 |
| Resort-week forecast WAPE | 0.249 |
| Seasonal baseline WAPE | 0.265 |
| Source domains represented | 12 |
| Reservation rows | 28,000 |
| Labor-shift rows | 40,866 |

## Engineering decisions

- Batch-first inference is the default because it lowers cost and simplifies replay, audit, and BI consumption.
- Every fact and mart declares its grain before aggregation to prevent duplicate multiplication and unstable metrics.
- Feature windows end before the prediction cutoff to prevent target leakage.
- Forecast candidates must satisfy an absolute accuracy threshold and beat the seasonal baseline before alias promotion.
- A failed candidate cannot replace the current `Champion`; the previous model version is retained as the rollback target.
- Development, staging, and production use separate Unity Catalog catalogs supplied to workloads at runtime.
- Local validation is reproducible without recurring cloud spend; managed deployment requires approved infrastructure and identities.

## Recommended review sequence

1. Read the architecture diagram and system design guide.
2. Run `python scripts/run_all.py` and `pytest -q`.
3. Review `databricks/resources/jobs.yml` for workflow ordering and environment parameters.
4. Review `train_waterfall.py` and `promote_waterfall.py` for acceptance and alias controls.
5. Start the FastAPI service and inspect `/ready`, `/model-info`, and `/score/member-churn`.
6. Review the operations, security, SLO, cost, and incident-response documents.
