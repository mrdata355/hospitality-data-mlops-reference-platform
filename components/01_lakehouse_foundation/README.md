# Lakehouse Foundation Component

**Ownership:** ingestion, conformance, dimensional modeling, data quality, lineage  
**Inputs:** members, resorts, reservations, stays, points, tours, contracts, campaigns, service cases, labor shifts  
**Outputs:** Bronze, Silver, dimensions, facts, and certified Gold inputs

The component preserves source records for replay, applies latest-record deduplication, normalizes types and statuses, validates business and foreign keys, and publishes conformed dimensions and atomic facts. Failed contracts stop publication before dependent models run.
