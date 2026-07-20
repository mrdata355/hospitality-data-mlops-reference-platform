# Operations Runbook

## Daily checks

1. Confirm source deliveries and expected batch identifiers.
2. Review Bronze and Silver row counts against trailing volume bands.
3. Confirm all critical data quality checks passed.
4. Confirm Gold and feature partitions are fresh before scoring begins.
5. Review batch score completion, prediction counts, and model alias used.
6. Review forecast error, member score distribution, drift, and API health.
7. Record or link any incident, manual replay, or approved exception.

## Pipeline replay

1. Identify the failed source domain and affected batch or partition.
2. Confirm the failure is deterministic and not caused by a partial file delivery.
3. Correct the source delivery or transformation defect.
4. Replay Bronze from the immutable landing object.
5. Re-run Silver only for the affected business keys or partition.
6. Rebuild dependent Gold and feature partitions.
7. Re-run scoring only after data contracts pass.
8. Compare replayed counts and metrics to the prior successful partition.

## Data quality failure

- Do not bypass a failed key, schema, or point-in-time check in production.
- Quarantine invalid records with batch, source, rule, and rejection reason.
- Preserve the last successful published table version.
- Notify the source owner when the defect is upstream.
- Open a controlled exception only when the business owner accepts the impact and an expiration time is recorded.

## Model rollback

1. Stop further promotion or traffic increase.
2. Run the environment-specific rollback workflow: `databricks bundle run hospitality_data_platform_model_rollback -t <target>`.
3. The workflow restores the latest recorded rollback target to the `Champion` alias and writes a rollback history record.
4. Re-run a representative smoke score with the approved contract payload.
5. Confirm output schema, latency, and prediction distribution.
6. Restart or redeploy the serving workload if required.
7. Record the failed version, cause, impact window, and rollback completion time.

## Online service recovery

- `/health` confirms that the process is running.
- `/ready` confirms that the model artifact is loaded and the service can accept traffic.
- A failed readiness probe removes the pod from service without immediately terminating it.
- Repeated liveness failures restart the pod.
- Horizontal scaling responds to CPU demand within configured minimum and maximum replicas.

## Forecast degradation

1. Confirm actuals are complete and aligned to the forecast grain.
2. Break error down by resort, market, and horizon.
3. Check for source volume shifts, calendar changes, or campaign changes.
4. Compare the active model to the seasonal baseline and prior model version.
5. Retrain only after feature and label integrity are confirmed.
6. Roll back when the prior model is materially safer.

## Local verification commands

```bash
python scripts/run_all.py
pytest -q
uvicorn hospitality_data_platform.api:app --app-dir src --port 8080
```
