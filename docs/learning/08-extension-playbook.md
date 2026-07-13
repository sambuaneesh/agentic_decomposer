# 08 - Extension Playbook

This chapter teaches how to change the framework without breaking the research
design. The goal is to help a new owner form their own ideas safely.

## The Golden Rule

Any extension should answer this first:

```text
Which artifact changes, and who consumes it?
```

If you cannot answer that, the extension is probably too vague.

## Add A New Evidence Signal

Example: repository co-change evidence for TC.

Steps:

1. Add fields to [evidence_pack.schema.json](../../schemas/evidence_pack.schema.json#L1),
   or create a new artifact if the signal is large.
2. Implement extraction under `agentic_decomposer/evidence/`.
3. Wire extraction in [EvidenceConstructorAgent](../../agentic_decomposer/agents/evidence_constructor.py#L53).
4. Add stable IDs if downstream agents need citations.
5. Update Generator and Refiner prompt context.
6. Update Quality Gate if references should be validated.
7. Add docs and no-API smoke tests.

Research payoff:

```text
TC is weak in the MVP because the LLM does not receive real repository-mining
signals. Co-change evidence directly targets that weakness.
```

## Add A Data Ownership Signal

Example: class-to-table access ownership for DTP and shared database concerns.

Where it belongs:

- deterministic evidence extraction;
- `evidence_pack.json` as a table/entity/access graph;
- Generator prompt for data-boundary reasoning;
- Quality Gate rule for shared database ownership;
- Refiner hints for splitting or merging data owners.

This would make the future Quality Governance Agent more concrete.

## Add A New Agent

Ask whether it really needs to be an agent. A new agent is justified when it has:

```text
separate responsibility
clear input artifact
clear output artifact
independent ablation value
```

Example: Repository Mining Agent.

Possible artifacts:

```text
repo_mining_model.json
class_cochange_matrix.csv
contributor_ownership.json
```

Implementation steps:

1. Add schema under `schemas/`.
2. Add layout paths in [RunLayout](../../agentic_decomposer/runs.py#L17).
3. Add agent class inheriting [BaseAgent](../../agentic_decomposer/agents/base.py#L26).
4. Insert stage in [ProcessController.run](../../agentic_decomposer/agents/process_controller.py#L41).
5. Pass artifact to Generator/Evaluator/Refiner where useful.
6. Add ablation flag if it supports a research question.
7. Update docs and experiment grid.

## Add A New Quality Gate Rule

Example: no service may own more than 40 percent of all classes unless justified.

Where to change:

1. Add fields to [QualityGateResult](../../agentic_decomposer/metrics/quality_gate.py#L33).
2. Compute the check in [run_quality_gate](../../agentic_decomposer/metrics/quality_gate.py#L101).
3. Add diagnostics in [DecompositionEvaluatorAgent](../../agentic_decomposer/agents/decomposition_evaluator.py#L196).
4. Update [evaluation_report.schema.json](../../schemas/evaluation_report.schema.json#L1).
5. Update docs.

Good quality rules are deterministic, explainable, and tied to a design concern.
Avoid philosophical rules that cannot be measured.

## Add A New Refiner Operation

Example: `extract_adapter_service`.

Steps:

1. Add a dataclass in [operations.py](../../agentic_decomposer/refinement/operations.py#L14).
2. Extend [parse_operation](../../agentic_decomposer/refinement/operations.py#L85).
3. Add a handler in [patcher.py](../../agentic_decomposer/refinement/patcher.py#L34).
4. Add it to `schemas/refinement_patch.schema.json`.
5. Add it to the Refiner prompt allowed operations.
6. Add evaluator diagnostic hints if a metric problem maps to it.

Do this only if existing operations cannot express the repair. Too many
operations make the Refiner harder to study.

## Add A New Benchmark System

Steps:

1. Add the codebase under `codebases/<new-system>`.
2. Add graph artifact under `graph-artifacts/<new-system>-class-dependency.json`.
3. Add metric-engine support and reference data in the sibling metric engine.
4. Extend [REPO_TO_APP](../../agentic_decomposer/paths.py#L57).
5. Update enum values in all schemas that restrict `system`.
6. Update CLI choices, docs, and experiment scripts.
7. Run deterministic evidence smoke test before LLM runs.

This is more than adding a folder. The metric engine and schemas must know the
new system too.

## Change A Schema Safely

Schema changes are breaking unless handled carefully.

Checklist:

- Update the schema.
- Update every producer.
- Update every consumer.
- Update sample docs.
- Run compile/import checks.
- Run no-API smoke tests that write and validate the artifact.
- Update migration notes if old run folders matter.

Use [validators.py](../../agentic_decomposer/artifacts/validators.py#L32) to
fail early when a producer drifts.

## Add A New Prompt Strategy

Example: `migration_feasibility_first`.

Steps:

1. Add prompt file under `prompts/`.
2. Add strategy to `_STRATEGIES` and `_STRATEGY_FILES` in
   [decomposition_generator.py](../../agentic_decomposer/agents/decomposition_generator.py#L21).
3. Add schema enum if `strategy` is restricted.
4. Add experiment variant if it supports a research question.
5. Update docs and expected interpretation.

Do not add prompt strategies just for variety. Each strategy should isolate a
meaningful architectural objective.

## Add Human-In-The-Loop Later

Human feedback belongs after the MVP, not before it.

A future design could add:

```text
architect_feedback.json
manual_constraints.json
interactive_refinement_session.json
```

The controller would consume those artifacts before Refiner or Generator calls.
The same file-based pattern still applies.

## How To Judge A New Idea

Use this decision table:

| Question | Good answer |
|----------|-------------|
| What weakness does it target? | A known metric or qualitative limitation. |
| Which artifact changes? | Named JSON or CSV artifact. |
| Who consumes it? | Specific agent or experiment script. |
| How is it ablated? | A flag or variant row. |
| How is success measured? | Metrics, diagnostics, stability, or cost. |
| Can it run without API for testing? | At least a deterministic smoke path. |

## Suggested Next Ideas

Strong next extensions:

- repository mining for TC/LC;
- database access graph for DTP and data ownership;
- stability analysis across repeated runs;
- Pareto-front candidate selection instead of one composite score;
- local deterministic graph refiner as a baseline against LLM Refiner;
- human architect review protocol for plausible-but-different decompositions.

Weaker first extensions:

- a UI before the experiment is stable;
- many new prompts without ablation value;
- a full Quality Governance Agent with subjective rules and no measurements;
- replacing the deterministic controller with an agent framework before the
  current design is fully tested.

## Final Ownership Exercise

Pick one idea and write a one-page mini design with these headings:

```text
Motivation
Artifact changes
Code changes
Experiment or ablation
Expected metric effect
Failure modes
No-API validation plan
```

If the design is easy to map to files, you understand the framework deeply.
