# Security Policy

This repository is an independent reference implementation using generated data.

## Do not commit

- customer or employee records
- production extracts
- credentials, tokens, passwords, or private keys
- internal proprietary architecture or source-system specifications
- `.env`, Databricks profiles, kubeconfigs, or cloud credential files

## Enforced repository controls

Pull-request automation performs:

- deterministic data and model regeneration
- Python compilation and correctness checks
- automated tests and model acceptance gates
- dependency vulnerability audit
- CodeQL static analysis
- non-root, read-only container execution
- health, readiness, version, model metadata, scoring, and metrics smoke tests
- release metadata, provenance, and SBOM generation for versioned images

Dependabot is configured for Python and GitHub Actions dependencies.

## Required managed-environment controls

A live deployment must additionally provide authorized identities, secret stores, registry policy, network policy enforcement, gateway authentication and rate limits, monitoring destinations, immutable image-digest promotion, vulnerability scanning, and change approval.

The public manifests and documentation describe those boundaries but do not claim that external controls are active in a live environment.

## Credential response

Rotate any credential immediately if it appears in a commit, build log, artifact, issue, or pull request. Remove access before rewriting history, then document the incident through the authorized private reporting channel.

## Reporting a concern

Open a private security report through GitHub when available. Do not publish suspected credentials, sensitive data, or exploit details in a public issue.

## Supported release

The current supported reference release is `1.1.x`.
