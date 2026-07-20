# Contributing

## Development workflow

1. Create a focused branch from `main` using `feature/`, `fix/`, `docs/`, or `chore/`.
2. Make one coherent engineering change.
3. Run `python scripts/run_all.py`.
4. Run `pytest -q`.
5. Confirm no generated data, model artifacts, or credentials are staged.
6. Open a pull request with validation evidence and rollback considerations.
7. Merge only after the required CI and model-acceptance checks pass.

## Commit conventions

Use an imperative subject that explains the engineering change, such as:

- `Add resort-week feature contract`
- `Harden API readiness behavior`
- `Enforce seasonal-baseline promotion gate`
- `Document model rollback procedure`

Avoid generic subjects such as `update files`, `initial upload`, or `publish project`.

## Pull-request evidence

Include:

- business or operational purpose
- tests and validation commands executed
- data-contract, schema, or feature-grain impact
- model-metric impact when relevant
- deployment, observability, and rollback notes
- confirmation that no secrets or production records were introduced
