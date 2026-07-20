# Generated Artifact Policy

Generated model packages, metrics, predictions, monitoring records, figures, and the local SQLite database are created during execution and excluded from source control.

This keeps validation reproducible: CI and reviewers must regenerate evidence from source rather than rely on committed outputs.
