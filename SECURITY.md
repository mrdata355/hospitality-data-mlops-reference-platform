# Security Policy

This repository is an independent reference implementation using generated data.

## Do not commit

- customer or employee records
- production extracts
- credentials, tokens, passwords, or private keys
- internal proprietary architecture or source-system specifications
- `.env`, Databricks profiles, kubeconfigs, or cloud credential files

## Preventive controls

- Keep generated datasets and trained artifacts outside Git history.
- Use GitHub secret scanning, dependency review, and automated dependency updates.
- Prefer managed identity or workload identity over long-lived client secrets.
- Use separate development, staging, and production identities and catalogs.
- Rotate any credential immediately if it appears in a commit, build log, artifact, or issue.

## Reporting a concern

Open a private security report through GitHub when available. Do not publish suspected credentials, sensitive data, or exploit details in a public issue.

## Supported release

The current supported reference release is `1.1.x`.
