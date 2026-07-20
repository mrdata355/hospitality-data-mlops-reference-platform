# GitHub Automation and Release Controls

This directory defines the repository controls that make the platform reproducible, reviewable, and safe to promote.

## Continuous integration

`workflows/ci.yml` executes the credential-free validation path on pull requests and protected-branch updates.

| CI stage | Control objective |
|---|---|
| Dependency installation | Recreate the supported Python environment |
| Python compilation | Detect syntax and import-time defects early |
| Deterministic pipeline | Regenerate source data, lakehouse outputs, features, models, predictions, and monitoring evidence |
| Automated tests | Validate dimensional grain, foreign keys, point-in-time features, API behavior, and deployment assets |
| Model acceptance gates | Enforce member-risk ROC AUC and forecast WAPE requirements |
| Release-asset checks | Confirm Databricks, rollback, Kubernetes, operations, and readiness assets are present |

## Pull-request standard

Every material change should include:

- a focused engineering purpose
- automated validation evidence
- data-contract or feature-grain impact
- model-metric impact when applicable
- deployment and rollback considerations
- confirmation that no credentials or production data were introduced

## Security boundary

Cloud credentials are intentionally excluded from source control. Authorized deployments must supply credentials through GitHub Actions secrets, workload identity, managed identity, or another approved secret-management mechanism.

The repository should never contain:

- customer or employee records
- production extracts
- tokens, passwords, private keys, or service-principal secrets
- `.env`, Databricks profiles, or kubeconfigs
- confidential source-system mappings or internal architecture

## Recommended branch protection

For an enterprise deployment, configure `main` to require:

- pull requests instead of direct pushes
- successful `platform-ci` checks
- at least one technical approval
- dismissal of stale approvals after new commits
- conversation resolution
- signed commits or verified organizational identity where required
- restricted force pushes and branch deletion

## Release principle

A code merge does not automatically authorize a production deployment. Production promotion additionally requires environment-specific identities, approved data contracts, security controls, model acceptance evidence, a rollback target, and change approval.
