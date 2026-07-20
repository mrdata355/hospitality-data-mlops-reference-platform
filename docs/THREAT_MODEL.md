# Threat Model

## Protected assets

- customer and employee data
- model artifacts and registry aliases
- feature and score tables
- deployment credentials and identities
- source code and release evidence
- operational logs and incident records

## Primary threats and controls

| Threat | Control |
|---|---|
| Credential exposure | Secret stores, workload identity, `.gitignore`, no secrets in YAML or logs |
| Unauthorized model promotion | Separate permissions, alias-based promotion, audit history |
| Data poisoning or malformed delivery | Immutable landing, schema checks, volume checks, quarantine, replay |
| Training-serving skew | Shared feature contracts, signatures, representative smoke scoring |
| Model extraction or API abuse | Authentication at ingress, rate limits, audit logs, minimal response payload |
| Excessive privileges | Group-based grants, service principals, least privilege, environment isolation |
| Supply-chain compromise | Dependabot, pinned release process, image scanning, immutable digests |
| Availability attack | HPA, PDB, topology spread, request limits, circuit breaking, autoscaling |
| Sensitive data leakage | Masking, tokenization, log redaction, restricted marts, retention controls |

## Trust boundaries

The public repository contains generated data only. Production source systems, secret stores, registries, workspaces, clusters, and serving environments are separate authorized trust zones.
