# SQL and Databricks Data Assets

This directory contains the parameterized lakehouse SQL and Spark ingestion assets used to translate generated or approved source data into governed analytical and machine-learning products.

The implementation is organized around six production concerns:

1. environment-scoped catalog and schema creation
2. incremental Bronze ingestion with source lineage and checkpoints
3. idempotent Silver conformance and Delta `MERGE`
4. conformed dimensions and atomic fact tables
5. Gold marts and point-in-time feature products
6. data-quality and forecast-monitoring evidence

## Directory

- [`databricks/`](databricks/README.md) contains the ordered SQL and PySpark assets, runtime parameters, input/output contracts, table grains, replay behavior, and execution guidance.

## Environment isolation

All managed objects are resolved through runtime catalog parameters rather than hard-coded environment names.

| Target | Example catalog |
|---|---|
| Development | `hospitality_data_platform_dev` |
| Staging | `hospitality_data_platform_staging` |
| Production | `hospitality_data_platform` |

This permits the same reviewed source to move across environments without editing table references.

## Local versus managed execution

The credential-free local path implements the same business grains and feature semantics in `src/hospitality_data_platform/`. The assets in this directory represent the managed Databricks and Delta Lake execution path and require an authorized workspace, identity, catalog permissions, source volumes, and secret configuration.
