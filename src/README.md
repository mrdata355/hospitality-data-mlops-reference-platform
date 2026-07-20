# Application Source

The `hospitality_data_platform` package contains the credential-free local reference implementation for synthetic source generation, Bronze and Silver processing, dimensional modeling, Gold marts, reusable point-in-time features, model training, monitoring, and FastAPI serving.

The package mirrors the business grains and feature semantics used by the managed Databricks path so reviewers can validate the full system without cloud credentials.

## Package

See [`hospitality_data_platform/README.md`](hospitality_data_platform/README.md) for module ownership, inputs, outputs, grains, error behavior, tests, and managed-platform equivalents.

## Design principles

- deterministic generated inputs
- modular domain responsibilities
- declared entity and time grains
- point-in-time feature correctness
- reproducible model evaluation
- explicit acceptance thresholds
- batch-first prediction outputs
- optional synchronous API serving
- observable model and forecast behavior
- no embedded credentials or production data

## Execution

The package is orchestrated through:

```bash
python scripts/run_all.py
```

or through the complete local validation target:

```bash
make validate
```
