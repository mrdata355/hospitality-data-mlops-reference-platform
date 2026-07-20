# Job Description Alignment

## Target roles

This evidence matrix maps the repository to two complementary responsibilities:

- Feature Engineer: reusable features, scalable Spark pipelines, quality, lineage, and training/inference consistency
- MLOps Engineer: model pipelines, CI/CD, registry, deployment, monitoring, Kubernetes, governance, and reliability

## Feature Engineer evidence matrix

| Job requirement | Implemented evidence | Reviewer path |
|---|---|---|
| Strong SQL | Parameterized Databricks SQL for schemas, MERGE, dimensional modeling, Gold marts, feature products, and monitoring | `sql/databricks/` |
| Strong Python | Modular generation, ingestion, dimensional modeling, marts, features, model training, monitoring, and API serving | `src/hospitality_data_platform/` |
| Spark and PySpark | Spark window features, joins, aggregations, Auto Loader ingestion, and Delta publication | `databricks/src_databricks/`, `sql/databricks/01_bronze_autoloader.py` |
| Databricks | Asset Bundle targets, jobs, runtime variables, Unity Catalog naming, and MLflow integration | `databricks/` |
| Reusable ML features | Member-month and resort-week feature products with documented grain and definitions | `src/hospitality_data_platform/features.py`, `docs/DATA_CONTRACTS.md` |
| Batch feature pipelines | Credential-free local pipeline and managed Databricks workflows | `scripts/run_all.py`, `databricks/resources/jobs.yml` |
| Streaming feature inputs | Auto Loader available-now ingestion pattern with checkpoints and schema location | `sql/databricks/01_bronze_autoloader.py` |
| Data modeling | Conformed dimensions, atomic facts, Gold products, and semantic metrics | `src/hospitality_data_platform/pipeline_dimensional.py`, `sql/databricks/03_dimensional_model.sql` |
| Data quality | Required-column, uniqueness, null, FK, feature-grain, missing-lag, drift, and model gates | `src/hospitality_data_platform/quality.py`, `tests/`, `sql/databricks/06_quality_and_monitoring.sql` |
| Feature lineage | Source file, batch, ingestion time, record hash, entity grain, and as-of cutoff | `pipeline_ingestion.py`, `DATA_CONTRACTS.md`, `TECHNICAL_SHOWCASE.md` |
| Documentation | Data dictionary, contracts, architecture, project ownership, runbooks, and ADRs | `docs/`, `components/` |
| Training/inference consistency | Shared feature names, point-in-time cutoffs, model signatures, API schema validation, and feature tests | `features.py`, `models.py`, `api.py`, `tests/test_features_and_models.py` |
| Feature Store readiness | Unity Catalog feature schema, point-in-time feature tables, reusable entities, and MLflow integration design | `databricks/`, `sql/databricks/05_feature_store.sql` |
| Data catalog | Separate Unity Catalog catalogs and documented ownership and access model | `databricks/databricks.yml`, `docs/SECURITY_GOVERNANCE.md` |
| Azure readiness | Azure-oriented Databricks configuration, AKS manifests, workload identity placeholder, and secret-store boundaries | `k8s/`, `docs/CREDENTIAL_SETUP.md` |

## MLOps Engineer evidence matrix

| Job requirement | Implemented evidence | Reviewer path |
|---|---|---|
| End-to-end ML pipeline | Feature build, train, acceptance, register, promote, score, monitor | `databricks/resources/jobs.yml` |
| CI/CD for ML | Pull-request pipeline generation, testing, model gates, and release-asset checks | `.github/workflows/ci.yml` |
| Model registry | MLflow registered model, immutable version, candidate evidence, and alias promotion | `train_waterfall.py`, `promote_waterfall.py` |
| Artifact versioning | Model artifacts, metrics, predictions, model version, run ID, and promotion history | `models.py`, `databricks/src_databricks/` |
| Reproducibility | Fixed seed, deterministic data generation, explicit features, chronological split, and CI execution | `config.py`, `data_generation.py`, `models.py` |
| Batch deployment | Delta forecast and member score outputs | `batch_score.py`, local prediction artifacts |
| Real-time deployment | Versioned FastAPI scoring service with validation and metadata | `src/hospitality_data_platform/api.py` |
| Kubernetes | Deployment, probes, resources, HPA, PDB, topology spread, NetworkPolicy, and ServiceAccount | `k8s/` |
| Monitoring | PSI, WAPE, bias, score mix, API counters, latency, data quality, and SLO definitions | `monitoring.py`, `api.py`, `docs/SLO_SLA.md` |
| Rollback | Previous model version retained as rollback target and dedicated rollback workflow | `promote_waterfall.py`, `rollback_waterfall.py`, `rollback.yml` |
| Security and compliance | Non-root container, read-only filesystem, dropped capabilities, secret exclusions, group access, and managed identity preference | `Dockerfile`, `k8s/`, `SECURITY.md`, `SECURITY_GOVERNANCE.md` |
| Observability | Health, readiness, Prometheus-format metrics, workflow status, drift and accuracy signals | `api.py`, `monitor.py`, `SLO_SLA.md` |
| Terraform/Bicep readiness | Infrastructure boundaries and deployment variables are documented; live IaC remains an authorized-environment extension | `docs/PRODUCTION_READINESS.md`, `docs/CREDENTIAL_SETUP.md` |

## Business-driver alignment

### Scalable Feature Store

The repository establishes the prerequisites for a governed Feature Store:

- reusable entity and as-of grains
- point-in-time event filtering
- shared definitions across training and inference
- Unity Catalog schemas
- feature contracts and documentation
- data-quality and drift checks
- scheduled feature builds

### Waterfall forecasting productionalization

The forecasting workflow includes:

- resort-week features
- chronological validation
- seasonal baseline
- absolute model threshold
- MLflow candidate version
- controlled `Champion` alias
- batch scoring
- accuracy monitoring
- rollback

### Self-service analytics and GenBI readiness

The platform reduces repeated engineering involvement by publishing:

- stable Gold products
- declared business grains
- documented semantic metrics
- reusable conversion, points, resort, labor, and forecasting outputs
- controlled data quality and lineage

These assets are suitable foundations for BI semantic layers and governed natural-language analytics. The repository intentionally does not claim a live GenBI deployment.

## Interview positioning

Use this statement:

> I built a credential-free, reproducible hospitality reference platform that connects governed lakehouse data, point-in-time reusable features, Waterfall-style forecasting, MLflow model controls, batch and API scoring, Kubernetes deployment definitions, and operational monitoring. It is designed around the exact handoff points between data engineering, feature engineering, data science, and MLOps.
