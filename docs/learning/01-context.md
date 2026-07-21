# Research Context

## Accepted ICSA Paper

The accepted paper asked an architecture-level question:

```text
Given a monolithic codebase, can an LLM infer architectural views and propose
service boundaries, and how do those boundaries compare against reference
microservice decompositions and existing decomposition tools?
```

It was not about generating microservice code. The output was a service
partition, not runnable services.

The old pipeline had three phases:

1. Summarise the monolith with one of seven summarisation strategies.
2. Generate architectural artifacts A1..A5 with the LLM and A6 with static
   analysis.
3. Ask the LLM for one JSON decomposition, then score it with Wang-style metrics.

The main result was nuanced:

```text
LLMs produce structurally clean, low-cycle decompositions, but they do not
reliably recover the reference or human-produced service boundaries.
```

That result motivates this framework. If one centralized LLM call is weak at
domain alignment, maybe a pipeline with separate evidence, domain, generation,
evaluation, and refinement roles can improve the weak spots.

## Wang et al. As The Benchmark Foundation

Wang et al.'s ASE 2024 comparison matters because it gives this project a
shared benchmark and metric language. The four systems are:

| System | Local folder | Metric-engine app name | Why it matters |
|--------|--------------|------------------------|----------------|
| 7ep-demo | `codebases/demo` | `demo` | Expert reference decomposition. |
| JPetStore | `codebases/jpetstore-6` | `jpetstore` | Small e-commerce system, good first debug target. |
| Spring PetClinic | `codebases/spring-petclinic` | `spring-petclinic` | Familiar domain with official microservice variant. |
| PartsUnlimitedMRP | `codebases/PartsUnlimitedMRP` | `partsunlimited` | Manufacturing/resource planning benchmark. |

Open [system mapping](../../agentic_decomposer/paths.py#L57) and notice that the
codebase folder names do not always match the metric-engine names. That mapping
is a tiny but important reproducibility detail.

## Metrics Used In The Story

The key metrics are:

| Metric | What it asks | Why reviewers care |
|--------|--------------|--------------------|
| MoJoFM | How close is the partition to the reference decomposition? | Measures recovery of known boundaries. |
| CiD | How cycle-free are service dependencies? | Captures the old LLM strength. |
| CMod / TurboMQ | Is static structural modularity good? | Captures cohesion/coupling over dependency graph. |
| BCP | Are services business-context pure? | Tests whether services mix use cases. |
| DI | Are use cases localized rather than scattered? | Tests domain separation. |
| TC / LC | Do services align with team/history signals? | Needs repository-mining signal to improve much. |
| DTP | Does database access stay coherent? | Future data-ownership direction. |

Open [metric extraction](../../agentic_decomposer/metrics/engine.py#L236) to see
how the framework maps the external engine output into these metric keys. The
important thing is that the framework reuses the metric engine. It does not
invent new MoJoFM, CiD, BCP, DI, or TC definitions.
