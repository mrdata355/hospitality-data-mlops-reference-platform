# Application Source

The `hospitality_data_platform` package contains the local reference implementation for ingestion, conformance, dimensional modeling, Gold marts, point-in-time features, model training, monitoring, and FastAPI serving.

The package is intentionally modular so local validation and managed Databricks execution preserve the same business grains, feature semantics, and model contracts.
