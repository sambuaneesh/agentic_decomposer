# Artifact Contracts

This chapter explains the JSON files that connect agents.

## The Core Pattern

The framework uses file-based contracts:

```text
agent reads JSON -> does one job -> validates JSON -> writes JSON
```

This is deliberate. In a research codebase, hidden in-memory agent state is a
liability. File artifacts make runs inspectable, resumable, comparable, and
ablatable.

Open [SchemaRegistry](../../agentic_decomposer/artifacts/schemas.py#L39) and
[validate](../../agentic_decomposer/artifacts/validators.py#L32). Those two
pieces are the contract enforcement layer.

## The Seven Main Schemas

| Artifact | Schema | Producer | Consumer |
|----------|--------|----------|----------|
| `run_config.json` | [run_config.schema.json](../../schemas/run_config.schema.json#L1) | CLI/controller | every agent |
| `evidence_pack.json` | [evidence_pack.schema.json](../../schemas/evidence_pack.schema.json#L1) | Evidence Constructor | Domain, Generator, Evaluator, Refiner |
| `domain_model.json` | [domain_model.schema.json](../../schemas/domain_model.schema.json#L1) | Domain Extractor ⚠️ (placeholder) | Generator, Refiner, Quality checks |
| `candidate_decompositions.json` | [candidate_decomposition.schema.json](../../schemas/candidate_decomposition.schema.json#L1) | Generator | Evaluator, Refiner, Controller |
| `evaluation_report.json` | [evaluation_report.schema.json](../../schemas/evaluation_report.schema.json#L1) | Evaluator | Refiner, Controller |
| `refinement_patch.json` | [refinement_patch.schema.json](../../schemas/refinement_patch.schema.json#L1) | Refiner | Patcher, audit trail |
| `final_output.json` | [final_output.schema.json](../../schemas/final_output.schema.json#L1) | Controller | experiment scripts, paper tables |

## Why Schemas Instead Of Loose Dicts

The LLM can produce malformed JSON, omit fields, invent class names, or drift
from the requested shape. Schemas catch structural drift early.

The Quality Gate catches semantic drift that schemas cannot catch alone, such as:

- a class assigned twice;
- a missing class;
- a dependency pointing at a service that does not exist;
- a service without evidence references;
- an evidence reference that does not exist in the current artifacts.

Read [run_quality_gate](../../agentic_decomposer/metrics/quality_gate.py#L101)
after reading the candidate schema. The schema says what a candidate must look
like; the gate says whether it is usable.

## Artifact 1: Run Config

Open [RunConfig dataclass](../../agentic_decomposer/config.py#L85) and
[build_run_config](../../agentic_decomposer/config.py#L147).

A run config answers:

```text
Which system?
Which model?
Which evidence mode?
How many candidates?
How many refinement rounds?
Which objective weights?
Which constraints?
Which ablation flags?
```

Example:

```json
{
  "system": "jpetstore-6",
  "model": "gpt-5",
  "evidence_mode": "llm",
  "summarisation_strategy": "80k_concat",
  "num_candidates": 3,
  "max_refinement_rounds": 1
}
```

The generated `run_id` is deterministic from system, model, strategy, and seed.
That makes output folders predictable.

## Artifact 2: Evidence Pack

The evidence pack normalizes A1..A6:

```text
A1 component diagram
A2 component overview
A3 API endpoints
A4 technology map
A5 dynamic interactions
A6 class dependency/call graph
```

Open [evidence pack schema](../../schemas/evidence_pack.schema.json#L1). Then
open [EvidenceConstructorAgent](../../agentic_decomposer/agents/evidence_constructor.py#L53).

The important fields are:

- `classes`: simple class inventory with stable `K_...` IDs;
- `components`: logical components with `C...` IDs;
- `api_endpoints`: endpoint evidence with `API_...` IDs;
- `dependency_edges`: static graph edges with `E_...` IDs;
- `dynamic_interactions`: scenario evidence with `S_...` IDs;
- `technology_map`: structured A4 data.

Those IDs are not decorative. They let later agents justify decisions by citing
specific evidence.

## Artifact 3: Domain Model

> **⚠️ TEMPORARY PLACEHOLDER — NOT CONCRETIZED.** The Domain Knowledge
> Extractor is a bare placeholder (single LLM call + prompt). Planned for
> proper development in V2. Treat as temporary scaffold.


The domain model is the answer to: what business capabilities might this code
represent?

Open [domain model schema](../../schemas/domain_model.schema.json#L1) and
[DomainExtractorAgent](../../agentic_decomposer/agents/domain_extractor.py#L35).

Key fields:

- `business_capabilities`: candidate capabilities such as Catalog Management;
- `bounded_context_hypotheses`: possible DDD-style contexts;
- `class_capability_matrix`: flat class-to-capability mapping for analysis.

Why this exists:

The old paper showed that LLM decompositions were weaker on domain separation
than on cycle avoidance. The Domain Agent explicitly gives the Generator a
business vocabulary before decomposition.

## Artifact 4: Candidate Decompositions

Open [candidate schema](../../schemas/candidate_decomposition.schema.json#L1)
and [Generator normalisation](../../agentic_decomposer/agents/decomposition_generator.py#L158).

A candidate is a service partition:

```json
{
  "candidate_id": "CAND_001",
  "strategy": "dependency_first",
  "services": [
    {
      "name": "CatalogService",
      "classes": [{"id": "Product"}, {"id": "Category"}],
      "responsibilities": ["Manage product catalog browsing"],
      "dependencies": ["OrderService"],
      "evidence_refs": ["C001", "API_001", "BC001"]
    }
  ],
  "rationale": "Prioritizes static dependency cohesion."
}
```

The candidate schema is richer than the old B0 decomposition shape. The final
controller still writes a B0-compatible `decomposition.json` for the metric
engine.

## Artifact 5: Evaluation Report

Open [evaluation schema](../../schemas/evaluation_report.schema.json#L1) and
[DecompositionEvaluatorAgent](../../agentic_decomposer/agents/decomposition_evaluator.py#L59).

Each candidate gets:

- `metrics`: MoJoFM, CiD, CMod, BCP, DI, TC, LC, DTP, num_services;
- `quality_gates`: deterministic structural checks;
- `composite_score`: internal selection score;
- `diagnostics`: actionable problems;
- `recommendation`: accept, refine, or reject.

This is the bridge between measurement and refinement.

## Artifact 6: Refinement Patch

Open [refinement patch schema](../../schemas/refinement_patch.schema.json#L1)
and [operation parser](../../agentic_decomposer/refinement/operations.py#L85).

The Refiner does not rewrite a whole decomposition. It proposes controlled
operations:

```text
move_class
split_service
merge_services
rename_service
add_dependency
remove_invalid_dependency
reassign_responsibility
```

This makes refinement auditable. You can say exactly what changed between the
initial candidate and the refined candidate.

## Artifact 7: Final Output

Open [final output schema](../../schemas/final_output.schema.json#L1) and
[final output writer](../../agentic_decomposer/agents/process_controller.py#L182).

The final output records:

- selected candidate ID;
- final metrics;
- comparison rows for initial and refined candidates;
- run metadata such as tokens, runtime, model, evidence mode, ablation flags;
- pointer to the B0-compatible `decomposition.json`.

## Stable ID Pattern

Open [IdMinter](../../agentic_decomposer/artifacts/ids.py#L35). It gives stable
prefixes to evidence items:

```text
component -> C001
api -> API_001
class_node -> K_001
edge -> E_001
scenario -> S_001
business capability -> BC001
```

Why not just cite names? Because names collide, change, and may be ambiguous.
IDs make evidence citations machine-checkable.
