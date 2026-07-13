# Agentic Decomposer Learning Path

This is the guided onboarding track for someone who has no prior context about
this repository, the accepted paper, Wang et al.'s benchmark, or the new agentic
framework.

Use this directory like a small course. Do not read the files randomly on the
first pass. Follow the chapters in order, open the linked source files, pause at
the checkpoints, and only move forward when you can explain the current piece in
your own words.

## What You Should Understand By The End

After completing this path, a reader should be able to:

- explain why this project is an architecture-level decomposition study, not a
  code-generation project;
- explain how the previous single-shot LLM pipeline becomes an iterative
  multi-agent framework;
- trace one run from CLI input to final output files;
- understand every JSON artifact and why file-based contracts were chosen;
- read each agent implementation and know its inputs, outputs, and failure modes;
- understand how Wang-style metrics are reused rather than reimplemented;
- run the MVP experiments on Linux and interpret the result table;
- propose a new evidence signal, agent, metric, or ablation without breaking the
  architecture.

## The One-Sentence Mental Model

The framework turns this:

```text
one LLM call -> one decomposition -> one evaluation
```

into this:

```text
evidence -> domain model -> multiple candidates -> metric evaluation -> local refinement -> re-evaluation -> final selection
```

The research claim is not that the agentic framework magically finds the single
correct decomposition. The claim is that specialization plus evaluate/refine
loops can make LLM decomposition more grounded, controllable, and measurable
than the earlier single-shot setup.

## How To Use This Guide

Each chapter has the same pattern:

1. Read the short motivation.
2. Open the linked files at the requested line anchors.
3. Answer the checkpoint questions before continuing.
4. Run only the optional no-API commands if you want to verify behavior locally.

When a link points into source code, read roughly 30 to 80 lines around the
anchor. The exact line is the start of the idea; the surrounding code is the
lesson.

## Linear Route

| Step | File | Purpose |
|------|------|---------|
| 0 | [01-research-context.md](01-research-context.md) | Understand the old paper, Wang et al., and the new research claim. |
| 1 | [02-repository-map-and-entrypoints.md](02-repository-map-and-entrypoints.md) | Learn the folders, CLI, config, path resolver, and run layout. |
| 2 | [03-artifact-contracts.md](03-artifact-contracts.md) | Understand the JSON contracts that connect agents. |
| 3 | [04-controller-and-run-lifecycle.md](04-controller-and-run-lifecycle.md) | Trace a complete run through the Process Controller. |
| 4 | [05-agents-deep-dive.md](05-agents-deep-dive.md) | Study each agent: evidence, domain, generation, evaluation, quality, refinement. |
| 5 | [06-metrics-quality-and-refinement.md](06-metrics-quality-and-refinement.md) | Understand Wang metrics, local quality checks, composite ranking, and patches. |
| 6 | [07-experiments-and-results.md](07-experiments-and-results.md) | Learn how MVP, all-system, and ablation experiments are run and interpreted. |
| 7 | [08-extension-playbook.md](08-extension-playbook.md) | Learn how to safely extend the framework and design new research ideas. |
| 8 | [10-llm-prompts-logging.md](10-llm-prompts-logging.md) | Understand LLM calls, prompt templates, JSON parsing, and logs. |
| 9 | [11-source-file-index.md](11-source-file-index.md) | File-by-file index for owning the source tree. |
| 10 | [12-next-versions-roadmap.md](12-next-versions-roadmap.md) | Plan V1/V2/V3 after initial Linux testing. |
| 11 | [13-literature-gap-analysis.md](13-literature-gap-analysis.md) | Literature-driven gap analysis and research priorities. |
| Reference | [09-glossary-and-debugging.md](09-glossary-and-debugging.md) | Use as a lookup table when terms blur or a run fails. |

## The Map Before The Territory

Before reading any code, hold this artifact flow in your head:

```text
CLI/config
  -> run_config.json
  -> evidence_pack.json
  -> domain_model.json
  -> candidate_decompositions.json
  -> evaluation_report.json
  -> quality_gate_report.json
  -> refinement_patch.json
  -> refined_candidate.json
  -> refined_evaluation_report.json
  -> final_output.json + decomposition.json
```

Every arrow is a file, not hidden memory. That is the most important design
choice in this repository.

## First Read-Along: Open These Five Files

Open these in order and skim only the linked areas:

1. [README overview](../../README.md#L1) for the package-level purpose.
2. [CLI parser](../../agentic_decomposer/cli.py#L28) for what users can run.
3. [ProcessController.run](../../agentic_decomposer/agents/process_controller.py#L41) for the whole pipeline.
4. [RunLayout](../../agentic_decomposer/runs.py#L17) for where artifacts are written.
5. [run_config schema](../../schemas/run_config.schema.json#L1) for the first artifact contract.

Checkpoint:

- Can you say what creates the run folder?
- Can you name the first three JSON artifacts in order?
- Can you explain why `decomposition.json` still exists even though we also have
  richer candidate artifacts?

## Fast No-API Sanity Commands

These commands do not call an LLM. They are useful while learning the code:

```powershell
cd agentic-experiments
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Resolve-Path .\agentic_decomposer).Path
python -m compileall -q agentic_decomposer\agentic_decomposer agentic_decomposer\experiments
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --dry-run
python agentic_decomposer\experiments\run_ablation.py --system demo --runs 1 --dry-run
```

On Linux, use the same package commands after `source .venv/bin/activate` and
`pip install -e agentic_decomposer`.

## Reading Rules For This Codebase

- Start from artifacts, not from implementation details. Ask: what file goes in,
  what file comes out?
- Treat every LLM call as a bounded implementation detail behind a schema.
- Treat Wang-style metrics as external truth: this framework wraps the metric
  engine, it does not redefine the research metrics.
- Treat the Quality Gate as the MVP version of future Quality Governance.
- Treat the Refiner as a controlled patch generator, not a second free-form
  decomposition generator.

## Common Beginner Confusions

**Is this generating microservice code?**

No. It produces architecture-level service partitions: service names, classes,
responsibilities, dependencies, evidence references, metrics, and rationale.

**Why so many JSON files?**

Because this is a research framework. If every agent writes a typed artifact, you
can reproduce runs, ablate agents, inspect failures, and compare variants.

**Why not just ask the LLM for the final answer?**

That was the old paper's experiment. This framework tests whether specialized
evidence/domain/generation/evaluation/refinement roles improve grounding and
controllability.

**Why keep `decomposition.json`?**

The old metric engine already expects that B0-compatible shape. The final output
writes it so new agentic results can be scored by the same pipeline as the old
baselines.

## Suggested Study Schedule

If you have one afternoon:

```text
Hour 1: research context + repository map
Hour 2: artifacts + controller lifecycle
Hour 3: agents + metrics/refinement
Hour 4: experiments + extension playbook
```

If you have a full day, run the no-API commands after each chapter and open the
produced dry-run folders under `agentic_decomposer/runs/`.

## After The First Pass

Return to the source with one concrete question. Good examples:

- How would I add repository co-change evidence for TC?
- How would I add a data-ownership quality gate?
- How would I make the Refiner compare several local patches?
- How would I add a fifth benchmark system?
- How would I produce a paper table from `final_output.json` rows?
- What should become V1 versus V2 after the first Linux results?

The goal is not to memorize every function. The goal is to own the shape of the
system well enough that new ideas feel local and implementable.

When the initial Linux MVP run is complete, continue with
[12-next-versions-roadmap.md](12-next-versions-roadmap.md) before adding new
agents or evidence signals. Then use
[13-literature-gap-analysis.md](13-literature-gap-analysis.md) to check whether
the proposed next step is grounded in the broader research landscape.
