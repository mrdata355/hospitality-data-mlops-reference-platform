# Kubernetes Model Serving

These manifests define the production-style serving controls for the member-risk API:

- rolling deployment with zero planned unavailability
- startup, readiness, and liveness probes
- horizontal autoscaling
- pod disruption protection
- topology spreading
- non-root execution and restricted capabilities
- workload identity and network-policy placeholders

Replace registry, identity, secret, and environment placeholders only through an authorized deployment process.
