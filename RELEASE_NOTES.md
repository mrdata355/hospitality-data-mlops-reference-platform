# Release Notes

## Version 1.1.0 - July 10, 2026

- Repositioned the package as an independently developed hospitality reference implementation using generated non-production data.
- Added a prominent boundary statement confirming that the package is not an approved or deployed production system for any real company.
- Added executive overview and implementation-evidence documents for technical leadership review.
- Parameterized Databricks Python and SQL assets by deployment catalog for dev, staging, and production isolation.
- Added an explicit resort-week feature-build task before forecast training.
- Added absolute WAPE and seasonal-baseline acceptance gates.
- Added immutable candidate registration, controlled `Champion` alias promotion, prior-version rollback evidence, and a rollback workflow.
- Added local and MLflow-backed model loading options for the FastAPI service while preserving the same API contract.
- Expanded dimensional, Gold, semantic-metric, feature, quality, and monitoring SQL assets.
- Expanded automated coverage to 20 passing tests, including deployment-asset and API validation checks.
- Updated the system design guide, deployment instructions, Kubernetes image version, CI workflow, verification record, and production-readiness checklist.
