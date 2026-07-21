# GitHub Automation and Release Controls

This directory defines the repository controls used to validate changes, retain evidence, manage dependencies, and publish versioned container images.

## Workflows

| Workflow | Trigger | Primary controls |
|---|---|---|
| `workflows/ci.yml` | pull requests and `main` updates | deterministic pipeline execution, automated tests, model acceptance gates, validated artifact handoff, restricted-container smoke testing, and concurrent API benchmarking |
| `workflows/quality.yml` | pull requests and `main` updates | changed-file Ruff checks, branch coverage, rolling-origin forecast backtesting, evidence-contract validation, and Python dependency auditing |
| `workflows/codeql.yml` | pull requests, `main`, weekly schedule | Python CodeQL analysis with the `security-extended` query suite |
| `workflows/release-image.yml` | approved release tags | multi-architecture GHCR image publication with provenance and SBOM output |

The workflows are intentionally separated so pipeline correctness, software quality, dependency security, static analysis, serving behavior, and release publication remain independently visible.

## Dependency maintenance

`dependabot.yml` checks Python packages, GitHub Actions, and Docker dependencies each week. Dependency changes arrive as normal pull requests and must pass the same validation gates as application changes.

## Pull-request standard

Every material change should document:

- the business, data, model, or platform outcome
- affected data contracts, grains, schemas, and interfaces
- automated validation performed
- model-metric impact when applicable
- runtime, cost, observability, migration, and rollback considerations
- confirmation that no credentials, production extracts, or confidential mappings were introduced

## Security boundary

Cloud credentials are excluded from source control. Authorized deployments must provide identity and secret material through approved platform controls such as GitHub Actions secrets, workload identity, managed identity, or an external secret manager.

The repository must not contain:

- customer or employee records
- production extracts
- tokens, passwords, private keys, or service-principal secrets
- `.env` files, Databricks profiles, or kubeconfigs
- confidential source-system mappings or internal company architecture

## Recommended branch protection

For an enterprise deployment, configure `main` to require:

- pull requests instead of direct pushes
- successful platform, quality, dependency-security, and CodeQL checks
- at least one technical approval
- dismissal of stale approvals after new commits
- resolution of review conversations
- restricted force pushes and branch deletion
- signed commits or verified organizational identity where required

## Release principle

A merge confirms that repository validation passed. It does not authorize production deployment. Production promotion additionally requires environment-specific identities, approved data contracts, target-environment testing, security review, model acceptance evidence, a rollback target, and change approval.
