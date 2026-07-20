# Repository Review Guide

Review the repository in this order:

1. `README.md` for scope, boundaries, and verification status.
2. `PROJECTS.md` for the six connected engineering projects.
3. `src/hospitality_data_platform/` for the local executable implementation.
4. `sql/databricks/` and `databricks/` for lakehouse and managed-platform execution.
5. `tests/` and `.github/workflows/ci.yml` for validation evidence.
6. `k8s/` for scalable model-serving controls.
7. `docs/` for architecture, security, SLOs, rollback, and production-readiness decisions.

The project is intentionally credential-free locally. Cloud deployment remains isolated behind approved identities and secret stores.
