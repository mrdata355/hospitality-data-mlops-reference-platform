# Incident Response

## Initial response

1. Assign severity and incident owner.
2. Record start time, affected capability, scope, and current business impact.
3. Stabilize the system before attempting a permanent fix.
4. Preserve logs, batch identifiers, table versions, model versions, and deployment metadata.
5. Communicate status on the severity-specific cadence.

## Common containment actions

- pause a failed workflow or downstream scoring job
- retain the prior Gold or feature table version
- switch the model alias to the last approved version
- remove an unhealthy API revision from traffic
- replay an affected batch from immutable landing data
- disable a non-critical source or feature through a controlled configuration flag

## Post-incident review

The review must include the timeline, triggering change, detection gap, impact, containment, root cause, corrective actions, and an owner and due date for each action. Corrective work is tracked until verification is complete.
