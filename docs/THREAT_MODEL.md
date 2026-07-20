# Threat Model

## Protected assets

- customer and employee data
- model artifacts and registry aliases
- feature and score tables
- deployment credentials and identities
- source code and release evidence
- operational logs and incident records

## Control status

| Status | Meaning |
|---|---|
| **Implemented** | Present in the public repository and exercised or statically validated by automation |
| **Reference design** | Configuration or workflow is included, but requires an authorized managed environment to execute |
| **External control** | Expected from the production identity, network, gateway, registry, or cloud platform |
| **Planned** | Required for production readiness but not yet implemented in this repository |

## Primary threats and controls

| Threat | Control | Status |
|---|---|---|
| Credential exposure | Secret exclusions, generated data, workload-identity service-account metadata, and no credentials in manifests | **Implemented** for repository boundaries; managed secret stores are **External controls** |
| Unauthorized model promotion | Acceptance gates, immutable model versions, alias promotion history, and rollback workflow | **Reference design** pending execution in an authorized MLflow and Unity Catalog environment |
| Data poisoning or malformed delivery | Schema, null, uniqueness, foreign-key, volume, grain, and deterministic replay checks | **Implemented** for generated inputs; production quarantine and source authorization are **Reference design** |
| Training-serving skew | Shared feature lists, signatures, API schema validation, model metadata, and representative smoke scoring | **Implemented** for the local artifact path; managed registry retrieval remains **Reference design** |
| Model extraction or API abuse | Minimal response contract and request identifiers | **Implemented**; ingress authentication, authorization, rate limits, and abuse detection are **External controls** |
| Excessive privileges | Non-root containers, dropped Linux capabilities, read-only filesystems, environment-separated catalogs, and workload identity metadata | Container controls are **Implemented**; cloud grants and service-principal policy are **Reference design** |
| Supply-chain compromise | Dependabot, pinned Python dependencies, CodeQL, dependency audit, OCI metadata, provenance, and SBOM generation | **Implemented**; image signing, vulnerability scanning, and deployment by digest are **Planned** |
| Availability attack | Readiness and liveness probes, resource limits, HPA, PDB, topology spread, and rolling updates | Manifests are **Implemented** and statically validated; managed gateway limits and circuit breaking are **External controls** |
| Sensitive data leakage | Generated public-safe data and explicit secret and production-data exclusions | **Implemented** for the repository; masking, tokenization, retention, and log-redaction policy are **External controls** |

## Trust boundaries

The public repository contains generated data only. Production source systems, secret stores, registries, workspaces, clusters, gateways, and serving environments are separate authorized trust zones.

Passing repository checks proves the behavior of the local deterministic path and validates the shape of managed deployment assets. It does not prove that external controls are configured in a live environment.
