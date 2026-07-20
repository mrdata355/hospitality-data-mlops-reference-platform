# Deployment and Release Management

## Scope and boundary

The local execution path is verified with generated non-production fixtures. The Databricks and Kubernetes assets are environment-ready reference definitions; production deployment requires approved workspace access, source volumes, identities, network policies, secret management, and change approval.

## Branch and promotion model

- Feature branches run deterministic pipeline, unit, contract, model acceptance, API, and production-asset tests.
- Pull requests require successful CI and code review.
- Merge to the protected main branch produces a versioned release candidate.
- Staging deployment runs the complete workflow against approved non-production data.
- Production promotion requires a release owner, validation evidence, rollback version, and change approval.

## Databricks release

Run from the `databricks` directory:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run hospitality_data_platform_pipeline -t dev

databricks bundle validate -t staging
databricks bundle deploy -t staging
databricks bundle run hospitality_data_platform_pipeline -t staging

databricks bundle validate -t prod
databricks bundle deploy -t prod
```

The active target supplies the Unity Catalog catalog to every workload at runtime:

| Target | Catalog |
|---|---|
| dev | `hospitality_data_platform_dev` |
| staging | `hospitality_data_platform_staging` |
| prod | `hospitality_data_platform` |

The forecast path executes in this order:

```text
build_waterfall_features
  -> train_waterfall
      -> acceptance gate
          -> register immutable candidate
              -> promote_waterfall (Champion alias)
                  -> batch_score
                      -> monitor
```

The candidate must satisfy the configured absolute WAPE threshold and beat the 52-week seasonal baseline. A rejected candidate raises a failed task and leaves the active alias unchanged. Promotion records the previous alias version as the rollback target.

## Parameterized SQL assets

SQL notebooks use Databricks named parameter markers such as `:catalog` and, where applicable, `:as_of_month`. The caller supplies those values from the deployment target rather than editing object names in source code.

## Container release

```bash
docker build -t hospitality-data-platform-api:1.1.0 .
docker run --rm -p 8080:8080 hospitality-data-platform-api:1.1.0
```

Kubernetes promotion sequence:

1. Deploy the immutable image tag or digest to staging.
2. Run health, readiness, schema, latency, and representative scoring tests.
3. Deploy a canary or blue/green production revision.
4. Compare error rate, latency, and prediction distribution.
5. Increase traffic only after the acceptance window passes.
6. Roll back to the prior image and model alias on threshold breach.

## API model source

The local service defaults to `MODEL_SOURCE=local` and loads the packaged joblib artifact. A managed deployment can use `MODEL_SOURCE=mlflow` with a registered `MODEL_URI`. Both paths preserve the same request and response contract.

## Release evidence

Each authorized production release records:

- source commit and release tag
- Databricks bundle version or container image digest
- active model name, version, and alias
- previous model version and rollback target
- input data contract version
- automated and staging validation results
- approver and deployment time
- change record and incident reference, when applicable
