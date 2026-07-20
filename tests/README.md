# Automated Validation

The test suite validates dimensional grains, foreign keys, point-in-time feature outputs, model acceptance thresholds, API contracts, deployment assets, environment isolation, promotion ordering, and rollback controls.

GitHub Actions regenerates all synthetic inputs and artifacts before executing the tests, which prevents committed outputs from masking pipeline failures.
