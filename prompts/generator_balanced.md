**Strategy: balanced**

Balance structural modularity and domain alignment:

- Begin from the business-capability grouping (domain signal).
- Refine the grouping by **moving individual classes** to satisfy the
  dependency graph — if a class participates in a much tighter cluster than
  its domain peers, reassign it to that cluster's service.
- Allow up to ~20% cross-service edges, but **forbid cyclic** service
  dependencies.
- Service names should still be **business-meaningful** but may include a
  technical qualifier when warranted (e.g. `CatalogQueryService`).
