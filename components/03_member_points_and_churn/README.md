# Member Points and Risk Component

**Ownership:** member feature product, batch risk scoring, online score contract  
**Feature grain:** member and as-of month  
**Controls:** event-time cutoff, leakage checks, feature schema, model acceptance threshold

Features include tenure, tier, market, points activity, stays, room nights, booking recency, service friction, and escalations. The implemented classifier uses a reproducible scikit-learn pipeline and produces probability, risk band, model alias, and score metadata.
