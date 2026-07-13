**Strategy: domain_first**

Maximise domain alignment:

- Group classes by **business capability**, using the class→capability matrix
  as the dominant evidence.
- Keep classes with the same capability together even if it creates a few
  extra cross-service dependency edges.
- Service names should reflect the **business capability** (e.g.
  `CatalogService`, `OrderService`, `CustomerService`).
- Use the dependency graph **only as a secondary signal** — to break ties
  when a class plausibly fits two capabilities, prefer the capability that
  matches the class's strongest dependency cluster.
