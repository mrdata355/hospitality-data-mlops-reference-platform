# Platform Capability Matrix

This matrix maps implemented platform capabilities to their primary repository evidence. It is intended as a technical index, not a job-description or interview guide.

## Data and feature engineering

| Capability | Implemented evidence | Primary paths |
|---|---|---|
| SQL and Spark SQL | Parameterized schemas, Delta `MERGE`, dimensional modeling, Gold products, feature tables, and monitoring SQL | `sql/databricks/` |
| Python engineering | Modular source generation, ingestion, dimensional modeling, feature engineering, model training, monitoring, and API serving | `src/hospitality_data_platform/` |
| PySpark processing | Windowed lag features, rolling aggregates, joins, feature publication, Auto Loader ingestion, and batch scoring | `databricks/src_databricks/`, `sql/databricks/01_bronze_autoloader.py` |
| Lakehouse modeling | Source-aligned Bronze, typed Silver, conformed dimensions, atomic facts, Gold marts, and semantic metrics | `pipeline_ingestion.py`, `pipeline_dimensional.py`, `pipeline_marts.py` |
| Reusable feature products | Member-month and resort-week features with declared entity and time grains | `features.py`, `sql/databricks/05_feature_store.sql` |
| Point-in-time correctness | Event-time cutoffs, shifted rolling windows, separate labels, and feature-list controls | `features.py`, `DATA_CONTRACTS.md`, `tests/test_features_and_models.py` |
| Data quality | Required-column, uniqueness, null, foreign-key, grain, lag completeness, drift, and model acceptance checks | `quality.py`, `tests/`, `sql/databricks/06_quality_and_monitoring.sql` |
| Lineage and reproducibility | Source file, batch ID, ingestion time, record hash, fixed seed, explicit cutoffs, and generated evidence | `pipeline_ingestion.py`, `config.py`, `scripts/run_all.py` |
| Batch and streaming patterns | Deterministic batch pipeline plus Auto Loader checkpoint and schema-location pattern | `scripts/run_all.py`, `sql/databricks/01_bronze_autoloader.py` |
| Catalog isolation | Separate development, staging, and production catalog variables | `databricks/databricks.yml` |

## Model lifecycle and serving

| Capability | Implemented evidence | Primary paths |
|---|---|---|
| End-to-end model workflow | Build features, train, validate, register, promote, score, and monitor | `databricks/resources/jobs.yml` |
| Reproducible training | Deterministic generation, explicit feature lists, chronological split, metrics, and model artifacts | `data_generation.py`, `models.py`, `train_waterfall.py` |
| Objective acceptance | Minimum ROC AUC, maximum WAPE, and seasonal-baseline comparison | `.github/workflows/ci.yml`, `tests/`, `train_waterfall.py` |
| Model registry controls | Immutable MLflow candidate version, evidence table, alias promotion, and promotion history | `train_waterfall.py`, `promote_waterfall.py` |
| Batch inference | Forecast publication and generated member-risk score outputs | `batch_score.py`, `artifacts/predictions/` |
| Synchronous inference | Versioned FastAPI contract with validation, request IDs, metadata, readiness, and metrics | `api.py` |
| Rollback | Previous model version recorded and restored through a dedicated workflow | `promote_waterfall.py`, `rollback_waterfall.py`, `rollback.yml` |
| Model monitoring | PSI, WAPE, bias, score distribution, data quality, service errors, and latency counters | `monitoring.py`, `monitor.py`, `api.py`, `SLO_SLA.md` |

## Platform operations

| Capability | Implemented evidence | Primary paths |
|---|---|---|
| CI validation | Full regeneration, sample synchronization, tests, model gates, and release-asset verification | `.github/workflows/ci.yml` |
| Containerization | Non-root image, deterministic dependencies, readiness health check, and local composition | `Dockerfile`, `docker-compose.yml` |
| Kubernetes availability | Rolling updates, startup/readiness/liveness probes, HPA, PDB, topology spread, resources, and Service | `k8s/` |
| Security boundaries | Secret exclusions, managed-identity preference, non-root execution, dropped capabilities, and NetworkPolicy | `.gitignore`, `SECURITY.md`, `k8s/` |
| Reliability | Last-successful publication, replay, rollback, SLOs, incident response, and recovery procedures | `OPERATIONS_RUNBOOK.md`, `INCIDENT_RESPONSE.md`, ADRs |
| Cost control | Batch-first inference, auto-termination, autoscaling, incremental processing, and compact serving products | `COST_CONTROL.md`, Databricks bundle definitions |
| Public validation evidence | Compact generated inputs, outputs, quality results, metrics, and acceptance status | `examples/` |

## Deployment boundary

The local implementation and CI path are credential-free and reproducible. Azure, Databricks, Unity Catalog, MLflow registry, and Kubernetes definitions are implementation-ready reference assets. Live deployment requires authorized infrastructure, identities, source contracts, security controls, load evidence, and operational approval.
