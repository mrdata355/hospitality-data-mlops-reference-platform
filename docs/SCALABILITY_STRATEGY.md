# Scalability Strategy

## Data scale

- Partition large facts by business date or event date, not by high-cardinality identifiers.
- Use Auto Loader checkpoints and incremental MERGE operations to avoid full reloads.
- Compact small files and apply clustering only to proven access paths.
- Materialize narrow Gold products for BI and model consumption instead of repeatedly scanning conformed Silver tables.
- Isolate replay and backfill workloads from daily production SLAs.

## Compute scale

- Use ephemeral Databricks job clusters with autoscaling and cluster policies.
- Separate ingestion, transformation, training, and serving workloads when their scaling patterns diverge.
- Keep feature builds distributed until the final training boundary.
- Use batch scoring for large populations and synchronous APIs only for latency-sensitive decisions.

## Serving scale

- Run at least three replicas across failure domains.
- Use readiness probes to remove unloaded models from traffic.
- Use a PodDisruptionBudget, topology spread, HPA, and zero-unavailable rolling updates.
- Use immutable image digests and immutable registered model versions.
- Add request-level timeouts, upstream retry budgets, and circuit breaking at the ingress or service mesh.

## Organizational scale

- Assign ownership by data product and platform capability.
- Version contracts and use compatibility rules for producer-consumer changes.
- Separate model development, model approval, and production deployment permissions.
- Standardize release evidence so teams can reuse the platform without weakening controls.

## Capacity planning signals

Track source volume, file count, shuffle size, state size, task skew, cluster utilization, feature-table growth, model load time, QPS, p95 and p99 latency, error rate, memory saturation, and cloud cost per successful business outcome.
