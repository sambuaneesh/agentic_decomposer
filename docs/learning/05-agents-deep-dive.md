# 05 - Agents Deep Dive

This chapter explains each agent in the framework. Read it with the source files
open. The goal is to understand each agent's job, inputs, outputs, and design
trade-offs.

## Shared Agent Contract

All agents inherit from [BaseAgent](../../agentic_decomposer/agents/base.py#L26).

Every agent has:

```text
name
config
layout
logger
_run(...)
```

The public `run(...)` method wraps `_run(...)` with logging and timing. The
specialized agent only implements its own work.

This pattern keeps the framework boring in a good way. Boring orchestration is
valuable in research software.

## Agent 1: Architectural Evidence Constructor

Open [EvidenceConstructorAgent](../../agentic_decomposer/agents/evidence_constructor.py#L53).

### Purpose

Build `evidence_pack.json`, the shared technical evidence base.

### Inputs

- system codebase under `codebases/<system>`;
- static dependency graph under `graph-artifacts/<system>-class-dependency.json`;
- selected evidence mode;
- selected summarisation strategy;
- optional external A1..A5 folder.

### Outputs

- `01_evidence/evidence_pack.json`;
- raw evidence support files such as LLM views or deterministic views.

### Modes

| Mode | Behavior |
|------|----------|
| `llm` | Summarise source, ask LLM for A1..A5, load A6 deterministically. |
| `deterministic` | Parse source for components/endpoints/technology/entities, load A6, no LLM. |
| `external` | Load A1..A5 from existing files, load A6 deterministically. |

Read these helpers:

- [source walker](../../agentic_decomposer/evidence/source_walker.py#L51);
- [summarise_codebase](../../agentic_decomposer/evidence/summariser.py#L186);
- [generate_llm_views](../../agentic_decomposer/evidence/llm_views.py#L46);
- [derive_components](../../agentic_decomposer/evidence/deterministic_views.py#L25);
- [load_dependency_graph](../../agentic_decomposer/evidence/dependency_graph_loader.py#L90);
- [load_external_views](../../agentic_decomposer/evidence/external_views.py#L35).

### Why This Design

The old paper's A1..A6 artifacts were central but produced as part of a single
pipeline. This framework gives them an owner. That makes it possible to ablate
evidence modes or replace A1..A5 with previous-paper artifacts.

### Watch For

- A6 is always deterministic.
- Deterministic mode is useful for no-API testing but has weaker semantic views.
- Evidence IDs are minted here, so downstream evidence citations depend on this
  stage.

## Agent 2: Domain Knowledge Extractor

> **⚠️ TEMPORARY PLACEHOLDER — NOT YET CONCRETIZED.**
>
> The Domain Knowledge Extractor has not been fully designed or built out. It is
> currently a bare placeholder: a single LLM call hardwired to the prompt at
> [`prompts/domain_extractor.md`](prompts/domain_extractor.md). The component
> is planned for proper development in V2 (see
> [docs/learning/12-next-versions-roadmap.md](docs/learning/12-next-versions-roadmap.md)),
> where richer evidence signals will feed into a comprehensive domain modeling stage.
> Until then, treat everything related to this component as a temporary scaffold.

Open [DomainExtractorAgent](../../agentic_decomposer/agents/domain_extractor.py#L35).

### Purpose

Turn technical evidence into a business/domain model.

### Inputs

- `evidence_pack.json`;
- model and prompt config;
- ablation flag `no_domain_agent`.

### Outputs

- `02_domain/domain_model.json`;
- `02_domain/class_capability_matrix.csv`.

### Why This Agent Exists

The old result showed that LLMs did well at cycle reduction but weaker at
reference/domain/team alignment. The Domain Agent explicitly attacks the domain
side of the problem before service generation.

### Behavior

Normal mode asks the LLM for:

- business capabilities;
- bounded-context hypotheses;
- domain vocabulary;
- class-to-capability mapping;
- evidence citations.

Ablation mode writes an empty schema-valid domain model. This lets the rest of
the pipeline run unchanged.

### Read Along

Open [domain prompt](../../prompts/domain_extractor.md#L1), then return to
[DomainExtractorAgent](../../agentic_decomposer/agents/domain_extractor.py#L35).

Checkpoint:

- What does the downstream Generator lose when the Domain Agent is ablated?
- Why is an empty schema-valid file better than a missing file?

## Agent 3: Decomposition Generator

Open [DecompositionGeneratorAgent](../../agentic_decomposer/agents/decomposition_generator.py#L45).

### Purpose

Generate candidate service decompositions.

### Inputs

- evidence pack;
- domain model;
- run config;
- strategy-specific prompt.

### Outputs

- `03_candidates/candidate_decompositions.json`;
- `03_candidates/schema_validation.json`.

### Candidate Strategies

Open [strategy list](../../agentic_decomposer/agents/decomposition_generator.py#L21).

The default rotation is:

```text
dependency_first -> domain_first -> balanced
```

The Generator makes separate LLM calls per candidate. That means if one
candidate fails JSON parsing or schema validation, retries can be isolated.

### Prompt Files

Read:

- [generator common prompt](../../prompts/generator_common.md#L1);
- [dependency-first directive](../../prompts/generator_dependency_first.md#L1);
- [domain-first directive](../../prompts/generator_domain_first.md#L1);
- [balanced directive](../../prompts/generator_balanced.md#L1).

### Normalisation

Open [candidate normalisation](../../agentic_decomposer/agents/decomposition_generator.py#L158).

The normaliser:

- keeps only known classes;
- removes duplicate class placements;
- adds leftover known classes to `UnassignedService` if unassigned classes are
  not allowed;
- drops dependency references to unknown services;
- ensures candidate metadata is consistent.

This is not a replacement for quality checking. It is a defensive cleanup layer
before schema validation.

### Why Multiple Candidates

The old paper had one decomposition per prompt. The new framework wants
trade-offs:

- a dependency-first candidate may have high CiD;
- a domain-first candidate may improve DI/BCP;
- a balanced candidate may be easier to migrate.

The Evaluator can then pick using metrics rather than trusting the first LLM
answer.

## Agent 4: Decomposition Evaluator

Open [DecompositionEvaluatorAgent](../../agentic_decomposer/agents/decomposition_evaluator.py#L59).

### Purpose

Score candidates and produce actionable feedback.

### Inputs

- candidate decompositions;
- evidence pack;
- domain model;
- external metric engine when available.

### Outputs

- `04_evaluation/evaluation_report.json`;
- `04_evaluation/candidate_ranking.csv`;
- temporary per-candidate decomposition files for metric engine input.

### What It Combines

For each candidate, the Evaluator:

1. runs local quality checks unless `--no-quality-gate` is active;
2. materializes B0-compatible decomposition JSON;
3. calls the metric engine if available;
4. computes an internal composite score;
5. builds diagnostics;
6. recommends accept, refine, or reject.

Read [evaluation loop](../../agentic_decomposer/agents/decomposition_evaluator.py#L80)
and [diagnostic builder](../../agentic_decomposer/agents/decomposition_evaluator.py#L196).

### Why It Is Mostly Tool-Based

Metrics should be deterministic. The Evaluator is not asking an LLM whether a
candidate is good. It uses Wang-style metrics plus local rules.

## Agent 5: Quality Gate

Open [QualityGateAgent](../../agentic_decomposer/agents/quality_gate.py#L18) and
[run_quality_gate](../../agentic_decomposer/metrics/quality_gate.py#L101).

### Purpose

Catch structural problems that metrics alone may not catch clearly.

### Checks

- every class assigned unless unassigned classes are explicitly allowed;
- no duplicate class assignments;
- no empty services;
- unique service names;
- simple class names only;
- dependencies point to existing services;
- no self-dependencies;
- each service has responsibilities or candidate rationale;
- each service cites evidence references;
- cited evidence references exist;
- service count obeys min/max constraints;
- cycle count is reported.

### Why This Is MVP Quality Governance

The full future Quality Governance Agent could check regulatory, performance,
security, data ownership, and stakeholder constraints. The MVP starts with a
rule-based gate because it is measurable and ablatable.

## Agent 6: Decomposition Refiner

Open [DecompositionRefinerAgent](../../agentic_decomposer/agents/decomposition_refiner.py#L25).

### Purpose

Improve a selected candidate using evaluator diagnostics, but only through
controlled operations.

### Inputs

- current candidate;
- evaluation report for that candidate;
- evidence pack;
- domain model;
- refinement round number.

### Outputs

- `05_refinement/refinement_patch.json`;
- `05_refinement/refined_candidate.json`.

### Prompt

Read [refiner prompt](../../prompts/refiner.md#L1). Notice that it asks for a
patch, not a fresh decomposition.

### Why Controlled Operations

If the Refiner rewrote the entire candidate, the experiment could not explain
what changed. A patch gives you a before/after story.

Allowed operations are defined in [operations.py](../../agentic_decomposer/refinement/operations.py#L14)
and applied in [patcher.py](../../agentic_decomposer/refinement/patcher.py#L34).

## Agent Responsibility Summary

| Agent | Type | Main artifact | Research reason |
|-------|------|---------------|-----------------|
| Process Controller | Tool | final output | Reproducible orchestration. |
| Evidence Constructor | Hybrid | evidence pack | Ground architecture reasoning in A1..A6. |
| Domain Extractor | Hybrid | domain model | Target old weakness in domain alignment. |
| Generator | LLM | candidates | Create multiple architectural alternatives. |
| Evaluator | Tool | evaluation report | Reuse metrics and produce diagnostics. |
| Quality Gate | Tool | quality report | Enforce structural validity and ablate governance. |
| Refiner | Hybrid | patch + refined candidate | Turn one-shot generation into an iterative loop. |

## Checkpoint Questions

- Which agents can call an LLM?
- Which agents are deterministic in the MVP?
- Which agent owns A6?
- Which agent writes `candidate_ranking.csv`?
- Which agent produces controlled operations?
- Why does `--no-domain-agent` not crash the Generator?

## Mini Exercise

Pick one class from a generated `evidence_pack.json`. Trace how it can appear in:

```text
classes -> domain_model class_capability_matrix -> candidate service classes -> quality gate assignment check -> final decomposition.json
```

If you can trace that path, you understand how the agents cooperate through
artifacts.
