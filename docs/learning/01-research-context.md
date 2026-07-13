# 01 - Research Context

This chapter explains why the code exists. Read it before studying individual
functions. Without the research context, the framework can look like a pile of
agents and JSON files. With the context, each design choice becomes fairly
natural.

## The Old Paper In One Minute

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

## Why The New Framework Exists

The old single-shot design compressed too much responsibility into one prompt:

```text
summary + A1..A6 -> one decomposition
```

That made it hard to answer research questions like:

- Was the failure caused by weak evidence?
- Was the domain model missing?
- Did the model produce multiple plausible decompositions but choose the wrong
  one?
- Would a metric-driven refiner improve the first result?
- Does the quality gate reduce invalid or hallucinated partitions?

The new framework separates those concerns:

```text
Evidence Constructor -> Domain Extractor ⚠️ (placeholder) -> Generator -> Evaluator -> Refiner -> Final selection
```

Each stage produces an artifact that can be inspected, validated, and ablated.
That is the main research design pattern.

## What The MVP Claim Can Test

The MVP can test this concrete claim:

```text
Compared with the previous single-shot LLM baseline, an agentic
multi-candidate evaluate/refine loop can improve decomposition quality,
evidence grounding, or controllability while preserving high cyclic independence.
```

It may not improve every metric. That is fine. The strong paper claim is not
"agentic wins everywhere". The better claim is:

```text
Agent specialization gives more controllable architectural trade-offs, and the
ablation study shows where improvements do or do not come from.
```

## Read-Along: Where This Motivation Appears In Code

1. Open [architecture introduction](../architecture.md#L1). This is the formal
   design framing.
2. Open [ablation grid](../ablation.md#L1). This is how the claim becomes an
   experiment.
3. Open [ProcessController.run](../../agentic_decomposer/agents/process_controller.py#L41).
   This is where the conceptual loop becomes executable code.
4. Open [run_ablation variants](../../experiments/run_ablation.py#L47). This is
   where B0/A1/A2/A3 and component ablations become concrete commands.

## Checkpoint Questions

Answer these before moving to the next chapter:

- Why is high CiD but low MoJoFM not automatically a failure?
- Why does the Domain Agent directly target a weakness of the old paper? (Note: Domain Extractor is currently a placeholder — see Stage 4 in mvp_roadmap.md.)
- Why is B0 reused instead of regenerated by this framework?
- Why are individual metrics reported instead of only a composite score?
- What would TC need that the current MVP does not yet provide?

## Mini Exercise

Write one paragraph explaining the project to a reviewer:

```text
The previous study showed _____. This framework tests _____ by adding _____.
The comparison is fair because _____. The expected result is not _____, but _____.
```

If you can fill that in without looking back, you understand the research
motivation well enough to read the code.
