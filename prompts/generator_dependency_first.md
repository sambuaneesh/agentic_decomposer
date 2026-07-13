**Strategy: dependency_first**

Maximise structural modularity:

- Group classes that **call, use, or create each other heavily** together.
  Heavily-coupled clusters should land in the same service.
- Minimise cross-service dependency edges.
- Prefer **cohesive subgraphs** over splitting tightly-coupled clusters.
- Use the dependency edge list above as the dominant evidence. The domain
  model is **secondary** — only break a cohesive subgraph if the domain
  signal is overwhelming.
- Cyclic service dependencies are unacceptable; reorganise to remove them.
