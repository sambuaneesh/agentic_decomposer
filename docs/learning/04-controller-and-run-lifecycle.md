# 04 - Controller And Run Lifecycle

This chapter teaches the execution spine of the system. If the agents are the
specialists, the Process Controller is the conductor.

## What The Controller Is And Is Not

The Process Controller is deterministic. It does not ask the LLM to reason. It
coordinates stages, passes artifacts, tracks runtime and token counts, and writes
the final run summary.

Open [ProcessController class](../../agentic_decomposer/agents/process_controller.py#L32).

The controller owns these questions:

```text
What runs first?
Where is the output written?
Which candidate is best?
Should refinement run?
Did refinement improve the result?
What final files should downstream scripts consume?
```

It does not own these questions:

```text
What is the domain model?
What service boundary is best?
What operation should fix a weak candidate?
What does MoJoFM mean?
```

Those belong to specialized agents or the external metric engine.

## The Run Method As A Story

Open [ProcessController.run](../../agentic_decomposer/agents/process_controller.py#L41)
and follow the code top to bottom.

The run lifecycle is:

```text
create folders
write run_config.json
run Evidence Constructor
run Domain Extractor
run Decomposition Generator
run Decomposition Evaluator
run standalone Quality Gate
run Refiner zero or more times
re-evaluate refined candidate
select final candidate
write final_output.json and decomposition.json
```

This is the main file to read when you feel lost.

## Stage 0: Create The Run Folder

The controller creates the run folder through [RunLayout.create](../../agentic_decomposer/runs.py#L67).

Why this happens at the start:

- Agents can safely write their outputs without checking folders.
- Logs have a stable destination.
- Dry-run mode can verify config and folder shape without API calls.

## Stage 1: Write The Config

Open [controller write config](../../agentic_decomposer/agents/process_controller.py#L152).

The config is validated before writing. That means every agent sees the same
frozen view of the run settings. No agent should secretly mutate experiment
parameters.

## Stage 2: Build Evidence

The controller calls the Evidence Constructor and stores the returned
`evidence_pack` in memory for the next agents. The important pattern is:

```text
agent returns output -> controller passes output forward -> agent also writes JSON
```

This gives both speed and auditability.

Read the call around [evidence stage](../../agentic_decomposer/agents/process_controller.py#L58).

## Stage 3: Extract Domain Knowledge

The Domain Extractor receives the evidence pack. If `--no-domain-agent` is on,
it writes an empty but schema-valid domain model. That matters because downstream
agents do not need separate code paths for missing files.

Read [DomainExtractorAgent](../../agentic_decomposer/agents/domain_extractor.py#L35)
after you finish this chapter.

## Stage 4: Generate Candidates

The Generator receives evidence plus domain model and produces one or more
candidates. In the MVP, the default is three candidates:

```text
dependency_first
domain_first
balanced
```

The controller does not inspect the prompt. It trusts the Generator to write a
schema-valid `candidate_decompositions.json`.

## Stage 5: Evaluate Candidates

The Evaluator scores each candidate and returns `best_candidate_id`.

Open [Evaluator class](../../agentic_decomposer/agents/decomposition_evaluator.py#L59).

The evaluator combines:

- metric-engine scores when available;
- local Quality Gate findings;
- diagnostics;
- internal composite score.

The controller uses the evaluator's best candidate rather than choosing directly
from LLM rationale.

## Stage 6: Standalone Quality Gate

The evaluator already uses quality checks internally. The standalone Quality Gate
also writes `quality_gate_report.json` for the selected candidate.

Read [QualityGateAgent](../../agentic_decomposer/agents/quality_gate.py#L18).

Why both?

- Evaluator needs quality results for ranking and recommendations.
- The standalone report gives a named artifact for audit and ablation.

When `--no-quality-gate` is enabled, both the standalone gate and evaluator
quality penalties are skipped. That makes the ablation honest.

## Stage 7: Refine And Re-Evaluate

The controller runs the Refiner only when:

```text
no_refiner is false
max_refinement_rounds > 0
a best candidate exists
```

The Refiner outputs a patch and a refined candidate. Then the Evaluator scores
that refined candidate.

Read [refiner loop](../../agentic_decomposer/agents/process_controller.py#L95).

The controller now checks whether refinement actually improved the report. Open
[improvement check](../../agentic_decomposer/agents/process_controller.py#L172).

This matters. A refinement loop should not publish a worse candidate just because
it exists.

## Stage 8: Write Final Output

Open [final output writer](../../agentic_decomposer/agents/process_controller.py#L182).

The controller writes two final files:

```text
06_final/final_output.json
06_final/decomposition.json
```

`final_output.json` is rich and research-friendly. `decomposition.json` is the
minimal B0-compatible shape expected by the existing metric engine.

Open [baseline conversion](../../agentic_decomposer/agents/process_controller.py#L258).
That helper strips a rich candidate down to:

```json
{
  "tool": {
    "decomposition": {
      "CatalogService": [{"id": "Product"}, {"id": "Category"}]
    }
  }
}
```

## The BaseAgent Pattern

Open [BaseAgent](../../agentic_decomposer/agents/base.py#L26) and
[BaseAgent.run](../../agentic_decomposer/agents/base.py#L43).

Every agent inherits the same wrapper behavior:

- attach an agent log file;
- log start and finish;
- time runtime;
- return an `AgentResult`;
- detach the file handler safely.

That is why individual agents focus on `_run` while cross-cutting mechanics stay
centralized.

## Error Philosophy

The controller does not hide failures. If a required artifact fails validation or
an agent raises, the run fails. This is intentional. Silent continuation with bad
research artifacts is worse than a visible failed run.

The exception is the metric engine: if the engine is unavailable, the Evaluator
can emit null metrics and warnings. That lets development continue on machines
that cannot run the full Java metric stack.

## Checkpoint Questions

- Why is the controller deterministic instead of LLM-backed?
- Why does the controller pass artifacts in memory and also rely on JSON files?
- Why does the Refiner produce a patch instead of a whole new decomposition?
- What prevents a worse refined candidate from being selected?
- Why are there two final files?

## Mini Exercise: Trace A Dry Run

Run:

```powershell
python -m agentic_decomposer run --system demo --dry-run
```

Then open:

```text
agentic_decomposer/runs/demo_gpt5_80kconcat_seed1/00_config/run_config.json
```

Question: which controller branches did dry-run skip? Confirm by reading
[CLI run one](../../agentic_decomposer/cli.py#L128).

## Ownership Exercise

Imagine you want to add a token-budget stopping condition. Where should it go?

A good answer:

- config field in `RunConfig` and schema;
- controller loop checks before calling Refiner again;
- final output records `stopping_reason = token_budget_exceeded`;
- docs and usage table updated.

If that answer feels obvious, you are starting to own the controller pattern.
