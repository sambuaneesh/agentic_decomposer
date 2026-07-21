# Source File Index

This is a file-by-file index for the framework source. Use it after the learning
path when you want to answer: "What is this file for, and when should I modify
it?"

The goal is not to repeat every line of code. The goal is to give each file a
home in your mental model.

## Entrypoints And Configuration

| File | Purpose | Open when... |
|------|---------|--------------|
| [__main__.py](../../agentic_decomposer/__main__.py) | Allows `python -m agentic_decomposer`. | CLI module execution is confusing. |
| [cli.py](../../agentic_decomposer/cli.py#L28) | Parses commands, merges CLI/config values, runs one or all systems. | Adding flags, config behavior, dry-run behavior. |
| [config.py](../../agentic_decomposer/config.py#L85) | Defines `RunConfig`, objectives, constraints, ablation flags, YAML merge. | Adding run settings or schema-backed config fields. |
| [paths.py](../../agentic_decomposer/paths.py#L31) | Resolves codebases, graph artifacts, metric engine, prompts, schemas, runs. | Moving folders, adding systems, debugging Linux paths. |
| [runs.py](../../agentic_decomposer/runs.py#L17) | Defines canonical run-folder layout and JSON read/write helpers. | Adding a new artifact file or folder. |
| [logger.py](../../agentic_decomposer/logger.py#L1) | Rich console logging and per-run file handlers. | Changing logs or debugging missing log files. |

## Agent Framework

| File | Purpose | Open when... |
|------|---------|--------------|
| [agents/base.py](../../agentic_decomposer/agents/base.py#L15) | `AgentResult` and `BaseAgent` wrapper for timing/logging. | Creating a new agent or changing common agent lifecycle. |
| [agents/process_controller.py](../../agentic_decomposer/agents/process_controller.py#L32) | Deterministic orchestrator for the full pipeline. | Changing stage order, stopping logic, final selection. |
| [agents/evidence_constructor.py](../../agentic_decomposer/agents/evidence_constructor.py#L53) | Builds normalized `evidence_pack.json`. | Changing A1..A6 construction or evidence modes. |
| [agents/domain_extractor.py](../../agentic_decomposer/agents/domain_extractor.py#L35) ⚠️ PLACEHOLDER — bare single-LLM-call scaffold. Not yet concretized. | Builds business capabilities and class-capability matrix. | Changing domain prompt, no-domain ablation, capability normalization. |
| [agents/decomposition_generator.py](../../agentic_decomposer/agents/decomposition_generator.py#L45) | Generates candidate decompositions by strategy. | Adding a generation strategy or changing candidate cleanup. |
| [agents/decomposition_evaluator.py](../../agentic_decomposer/agents/decomposition_evaluator.py#L59) | Scores candidates, runs quality checks, builds diagnostics. | Changing metric integration, recommendation logic, ranking CSV. |
| [agents/quality_gate.py](../../agentic_decomposer/agents/quality_gate.py#L18) | Writes standalone selected-candidate quality report. | Changing quality report artifact behavior. |
| [agents/decomposition_refiner.py](../../agentic_decomposer/agents/decomposition_refiner.py#L25) | Asks LLM for controlled refinement patch and applies it. | Changing refinement prompt or patch normalization. |

## Evidence Layer

| File | Purpose | Open when... |
|------|---------|--------------|
| [evidence/source_walker.py](../../agentic_decomposer/evidence/source_walker.py#L29) | Walks Java files, extracts package/type info and stereotypes. | Parser misses classes or stereotypes. |
| [evidence/summariser.py](../../agentic_decomposer/evidence/summariser.py#L48) | Implements 30k/50k/80k concat/aggregate/hierarchical summaries. | Changing summarisation strategy behavior. |
| [evidence/llm_views.py](../../agentic_decomposer/evidence/llm_views.py#L25) | Generates A1..A5 from summaries via LLM. | Evidence LLM prompt/output changes. |
| [evidence/deterministic_views.py](../../agentic_decomposer/evidence/deterministic_views.py#L25) | Derives components, endpoints, technology, persistence from source. | Improving no-API evidence or parser heuristics. |
| [evidence/external_views.py](../../agentic_decomposer/evidence/external_views.py#L24) | Loads pre-existing A1..A5 files. | Reusing old paper artifacts or hand-curated evidence. |
| [evidence/dependency_graph_loader.py](../../agentic_decomposer/evidence/dependency_graph_loader.py#L43) | Loads A6 class dependency graph from `graph-artifacts`. | Graph artifact shape changes or edges look wrong. |

## LLM And Helper Layer

| File | Purpose | Open when... |
|------|---------|--------------|
| [llm/client.py](../../agentic_decomposer/llm/client.py#L14) | LiteLLM wrapper, token extraction, JSONL prompt logging. | Adding retries, changing provider behavior, debugging tokens. |
| [helpers/json_parsing.py](../../agentic_decomposer/helpers/json_parsing.py#L15) | Robust extraction of JSON from LLM responses. | LLM returns fenced JSON or prose around JSON. |

## Artifacts And Validation

| File | Purpose | Open when... |
|------|---------|--------------|
| [artifacts/schemas.py](../../agentic_decomposer/artifacts/schemas.py#L39) | Loads schema files by logical name. | Adding a new schema. |
| [artifacts/validators.py](../../agentic_decomposer/artifacts/validators.py#L17) | Wraps jsonschema validation with readable errors. | Debugging schema failures. |
| [artifacts/ids.py](../../agentic_decomposer/artifacts/ids.py#L35) | Mints stable IDs like `C001`, `API_001`, `K_001`, `E_001`. | Adding a new evidence ID type. |

## Metrics And Quality

| File | Purpose | Open when... |
|------|---------|--------------|
| [metrics/engine.py](../../agentic_decomposer/metrics/engine.py#L37) | Subprocess wrapper for Wang-style metric engine and metric extraction. | Metrics are null, Java path fails, engine output changes. |
| [metrics/quality_gate.py](../../agentic_decomposer/metrics/quality_gate.py#L33) | Local deterministic quality checks. | Adding a structural or grounding rule. |
| [metrics/composite_score.py](../../agentic_decomposer/metrics/composite_score.py#L33) | Internal candidate ranking score. | Changing controller selection weights or score formula. |

## Refinement

| File | Purpose | Open when... |
|------|---------|--------------|
| [refinement/operations.py](../../agentic_decomposer/refinement/operations.py#L14) | Dataclasses and parser for allowed patch operations. | Adding a new refinement operation. |
| [refinement/patcher.py](../../agentic_decomposer/refinement/patcher.py#L26) | Deterministically applies operations to candidate copies. | Patch behavior is wrong or a new operation needs a handler. |

## Experiment Scripts

| File | Purpose | Open when... |
|------|---------|--------------|
| [experiments/run_mvp.py](../../experiments/run_mvp.py#L1) | Single-system MVP wrapper around CLI. | Running first JPetStore/demo MVP trial. |
| [experiments/run_all_systems.py](../../experiments/run_all_systems.py#L1) | Sequential all-four-system wrapper. | Running the four benchmark systems. |
| [experiments/run_ablation.py](../../experiments/run_ablation.py#L1) | B0/A1/A2/A3 plus component ablation grid and CSV rows. | Producing the main comparison table. |

## Schemas

| Schema | What It Protects |
|--------|------------------|
| [run_config.schema.json](../../schemas/run_config.schema.json#L1) | Experiment settings and reproducibility metadata. |
| [evidence_pack.schema.json](../../schemas/evidence_pack.schema.json#L1) | A1..A6 normalized evidence structure. |
| [domain_model.schema.json](../../schemas/domain_model.schema.json#L1) ⚠️ (placeholder component) | Business capabilities and class-capability mapping. |
| [candidate_decomposition.schema.json](../../schemas/candidate_decomposition.schema.json#L1) | Candidate service partitions. |
| [evaluation_report.schema.json](../../schemas/evaluation_report.schema.json#L1) | Metrics, quality gates, diagnostics, recommendations. |
| [refinement_patch.schema.json](../../schemas/refinement_patch.schema.json#L1) | Controlled refinement operation list. |
| [final_output.schema.json](../../schemas/final_output.schema.json#L1) | Final run summary and metric comparison rows. |

## Prompts

| Prompt | Used By | Change Carefully Because... |
|--------|---------|-----------------------------|
| [evidence_views.md](../../prompts/evidence_views.md) | Evidence Constructor | It changes A1..A5 evidence produced by LLM. |
| [domain_extractor.md](../../prompts/domain_extractor.md) | Domain Extractor ⚠️ (placeholder prompt) | It changes domain capabilities and class mappings. |
| [generator_common.md](../../prompts/generator_common.md) | Generator | It changes the core candidate contract shown to the model. |
| [generator_dependency_first.md](../../prompts/generator_dependency_first.md) | Generator | It changes dependency-first candidate behavior. |
| [generator_domain_first.md](../../prompts/generator_domain_first.md) | Generator | It changes domain-first candidate behavior. |
| [generator_balanced.md](../../prompts/generator_balanced.md) | Generator | It changes balanced candidate behavior. |
| [refiner.md](../../prompts/refiner.md) | Refiner | It changes repair operations and refinement behavior. |

## Configs

| Config | Use |
|--------|-----|
| [mvp_jpetstore.yaml](../../configs/mvp_jpetstore.yaml) | First real MVP run on JPetStore. |
| [mvp_all_systems.yaml](../../configs/mvp_all_systems.yaml) | All-four-system profile. |
| [ablation/no_domain.yaml](../../configs/ablation/no_domain.yaml) | Domain Agent (placeholder) ablation. |
| [ablation/no_refiner.yaml](../../configs/ablation/no_refiner.yaml) | Refiner ablation. |
| [ablation/no_quality_gate.yaml](../../configs/ablation/no_quality_gate.yaml) | Quality Gate ablation. |

## If You Want To Modify Something

Use this routing table:

| Desired change | Start here |
|----------------|------------|
| Add a CLI flag | `cli.py`, `config.py`, `run_config.schema.json`, `usage.md`. |
| Add an artifact | `runs.py`, new schema, producer agent, consumer agents. |
| Add evidence | `evidence/`, `EvidenceConstructorAgent`, `evidence_pack.schema.json`. |
| Add a candidate strategy | Generator prompt files, `_STRATEGIES`, candidate schema enum. |
| Add a metric | metric engine wrapper, evaluation schema, docs. |
| Add a quality rule | `metrics/quality_gate.py`, evaluator diagnostics, evaluation schema. |
| Add a refiner operation | `operations.py`, `patcher.py`, refinement schema, refiner prompt. |
| Add a benchmark system | `paths.py`, schemas, metric engine support, docs, tests. |
