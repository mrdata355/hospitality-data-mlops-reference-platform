# GitHub Automation

This directory contains repository automation and contribution controls.

- `workflows/ci.yml` executes the deterministic pipeline, automated tests, model acceptance gates, and release-asset checks.
- Dependency updates and pull-request templates belong here when enabled.
- Cloud deployment credentials are intentionally excluded and must be supplied through approved GitHub Actions secrets.
