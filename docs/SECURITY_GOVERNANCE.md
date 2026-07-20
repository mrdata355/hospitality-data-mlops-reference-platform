# Security and Governance

## Access model

- Unity Catalog grants are assigned to groups, not individual users.
- Production write access is limited to service principals and approved operational roles.
- BI consumers receive read access only to certified serving tables and views.
- Model promotion and production deployment require separate permissions from model development.

## Sensitive data handling

- Direct identifiers are excluded from model features and broad analytical marts unless explicitly approved.
- PII is masked or tokenized for non-production environments.
- Logs and exception messages must not contain emails, phone numbers, tokens, or full request payloads.
- Data retention and deletion rules apply to landing, tables, checkpoints, artifacts, and backups.

## Secrets and identity

- Azure managed identities and service principals are preferred over static credentials.
- Secrets are stored in Key Vault, Databricks secret scopes, or Kubernetes secrets.
- Secret values are never committed to source control or embedded in notebooks, YAML, model artifacts, or logs.

## Auditability

- Table and model ownership is documented.
- Data lineage is retained from source through Gold and features.
- Model runs record code version, data reference, parameters, metrics, signature, and artifacts.
- Production releases retain approvals, deployment identifiers, and rollback targets.
