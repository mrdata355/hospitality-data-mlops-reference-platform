# Contributing

## Development workflow

1. Create a branch from `main`.
2. Make a focused change.
3. Run `python scripts/run_all.py`.
4. Run `pytest -q`.
5. Confirm no generated data, artifacts, or credentials are staged.
6. Open a pull request with validation evidence and rollback considerations.

## Commit conventions

Use an imperative subject such as:

- `Add resort-week feature contract`
- `Harden API readiness behavior`
- `Document model rollback procedure`

## Pull-request evidence

Include:

- business or operational purpose
- tests executed
- data-contract or schema impact
- model-metric impact when relevant
- deployment and rollback notes
