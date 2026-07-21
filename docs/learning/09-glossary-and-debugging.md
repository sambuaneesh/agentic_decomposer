# Glossary And Debugging Guide

## Glossary

| Term | Meaning in this repository |
|------|----------------------------|
| A1 | Component diagram or component-level structural view. |
| A2 | Component overview table. |
| A3 | API endpoints. |
| A4 | Technology map. |
| A5 | Dynamic interactions or scenario-style behavior. |
| A6 | Static class dependency/call graph, loaded from `graph-artifacts/`. |
| B0 | Previous single-shot LLM baseline, reused from `results/`. |
| A1_gen_only | Agentic variant with one generated candidate and no refinement. |
| A2_eval_select | Agentic variant with three candidates and evaluator selection, no refinement. |
| A3_refined | Full MVP: three candidates, evaluator selection, one refinement round. |
| Evidence pack | Normalized A1..A6 artifact consumed by downstream agents. |
| Domain model | Business capabilities, bounded contexts, and class-capability mapping. |
| Candidate | One proposed service decomposition. |
| Quality Gate | Deterministic structural validation and grounding checks. |
| Composite score | Internal ranking score, not the main paper result. |
| Refiner patch | Controlled operations that modify a candidate locally. |
| Emit-only mode | Evaluator writes decomposition and null metrics when metric engine is unavailable. |

## Which File Should I Open?

| Question | File |
|----------|------|
| How does the run start? | [cli.py](../../agentic_decomposer/cli.py#L28) |
| What order do agents run in? | [process_controller.py](../../agentic_decomposer/agents/process_controller.py#L41) |
| Where are artifacts written? | [runs.py](../../agentic_decomposer/runs.py#L17) |
| Where are codebase paths resolved? | [paths.py](../../agentic_decomposer/paths.py#L31) |
| What validates schemas? | [validators.py](../../agentic_decomposer/artifacts/validators.py#L32) |
| How is evidence built? | [evidence_constructor.py](../../agentic_decomposer/agents/evidence_constructor.py#L53) |
| How are candidates generated? | [decomposition_generator.py](../../agentic_decomposer/agents/decomposition_generator.py#L45) |
| How are metrics called? | [engine.py](../../agentic_decomposer/metrics/engine.py#L87) |
| How are quality rules checked? | [quality_gate.py](../../agentic_decomposer/metrics/quality_gate.py#L101) |
| How is refinement applied? | [patcher.py](../../agentic_decomposer/refinement/patcher.py#L34) |
| How are ablations run? | [run_ablation.py](../../experiments/run_ablation.py#L47) |

## Debugging By Symptom

### CLI says config or system is invalid

Open:

- [CLI main](../../agentic_decomposer/cli.py#L144);
- [build_run_config](../../agentic_decomposer/config.py#L147);
- [run config schema](../../schemas/run_config.schema.json#L1).

Check:

- Did you pass `--system` or use a config with `system`?
- Is the system one of the four schema enum values?
- Are you invoking from the repo root or setting `PYTHONPATH` correctly?

### Evidence stage fails

Open:

- `logs/agent_evidence_constructor.log`;
- [EvidenceConstructorAgent](../../agentic_decomposer/agents/evidence_constructor.py#L53);
- [dependency graph loader](../../agentic_decomposer/evidence/dependency_graph_loader.py#L90).

Check:

- Does `graph-artifacts/<system>-class-dependency.json` exist?
- Does the selected evidence mode require an API call?
- For `external`, does the external views folder have the expected layout?

### Generator produces no valid candidates

Open:

- `03_candidates/schema_validation.json`;
- `logs/llm_calls.jsonl`;
- [generator common prompt](../../prompts/generator_common.md#L1);
- [candidate schema](../../schemas/candidate_decomposition.schema.json#L1).

Check:

- Did the LLM return strict JSON?
- Are class names simple names, not FQNs?
- Are service dependencies names of services in the same candidate?
- Are evidence references valid IDs?

### Evaluation has null metrics

Open:

- `04_evaluation/evaluation_report.json`;
- [metric engine wrapper](../../agentic_decomposer/metrics/engine.py#L87);
- [metric engine docs](../metric_engine.md#L1).

Check:

- Is `../src/metrics/scripts/evaluate_decomposition.py` present on Linux?
- Is Java available on PATH or via `AGENTIC_DECOMPOSER_JAVA_HOMES`?
- Did the wrapper fall back to emit-only mode?

### Candidate rejected by Quality Gate

Open:

- `04_evaluation/evaluation_report.json`;
- `04_evaluation/quality_gate_report.json`;
- [quality gate checks](../../agentic_decomposer/metrics/quality_gate.py#L101).

Look for:

```text
missing_classes
duplicate_class_assignments
duplicate_service_names
invalid_evidence_refs
services_missing_evidence_refs
service_count_within_bounds
```

### Refinement does not change final output

Open:

- `05_refinement/refinement_patch.json`;
- `05_refinement/refined_evaluation_report.json`;
- [controller improvement check](../../agentic_decomposer/agents/process_controller.py#L172).

A refined candidate is only selected if it improves status or composite score.
This is intended behavior.

## No-API Validation Ladder

Run these from easiest to strongest:

```powershell
python -m compileall -q agentic_decomposer\agentic_decomposer agentic_decomposer\experiments
python -m agentic_decomposer run --system demo --dry-run
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --dry-run
python -m agentic_decomposer run --config configs/mvp_all_systems.yaml --system all --dry-run
python agentic_decomposer\experiments\run_ablation.py --system demo --runs 1 --dry-run
```

If those pass, CLI/config/layout/experiment wiring is healthy. They do not prove
LLM prompts or the external metric engine will succeed.

## Linux Real-Run Checklist

Before running expensive experiments:

- preserve sibling layout: `agentic-experiments/` next to `src/`;
- create and activate a venv;
- install requirements;
- install package editable with `pip install -e agentic_decomposer`;
- set LLM provider key for the selected model;
- confirm Java is available;
- dry-run config and ablation scripts;
- start with JPetStore only;
- inspect one full run before all-system batch.
