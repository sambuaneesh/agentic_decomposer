# Repository Map And Entrypoints

## Three Layers Of The Workspace

```text
agentic-experiments/
  codebases/                 input monoliths
  graph-artifacts/           existing static class dependency graphs
  results/                   old baseline decompositions
  scripts/                   existing analysis scripts
  agentic_decomposer/        new framework

../src/metrics/scripts/      external Wang-style metric engine
```

The current framework does not own the benchmark systems or metric engine. It reads
those assets and writes new run outputs.

## Framework Layout

Open [framework README layout](../../README.md#L38) first. Then map that to

| Folder | Role |
|--------|------|
| `agentic_decomposer/agentic_decomposer/agents` | Agent implementations and controller. |
| `agentic_decomposer/agentic_decomposer/evidence` | Source scanning, summarisation, static and external evidence loaders. |
| `agentic_decomposer/agentic_decomposer/metrics` | Metric engine wrapper, quality gate, composite score. |
| `agentic_decomposer/agentic_decomposer/refinement` | Controlled patch operations and deterministic patch application. |
| `agentic_decomposer/schemas` | JSON artifact contracts. |
| `agentic_decomposer/prompts` | Prompt templates for LLM-backed agents. |
| `agentic_decomposer/experiments` | Scripted MVP and ablation runs. |
| `agentic_decomposer/runs` | Generated run folders, gitignored. |

## Entrypoint 1: The CLI

Execution usually starts here:

```powershell
python -m agentic_decomposer run --system jpetstore-6 --model gpt-5
```

Read [CLI parser](../../agentic_decomposer/cli.py#L28). Notice the important
flags:

- `--system`: one codebase or `all`;
- `--model`: LiteLLM model string;
- `--evidence-mode`: `llm`, `deterministic`, or `external`;
- `--num-candidates`: how many decompositions the Generator produces;
- `--max-refinement-rounds`: how many local refinement passes are allowed;
- `--no-domain-agent`, `--no-quality-gate`, `--no-refiner`: ablation controls;
- `--config`: YAML profile;
- `--dry-run`: create config/run folder without invoking agents.

Then read [CLI config builder](../../agentic_decomposer/cli.py#L102). This is
where CLI flags are merged with YAML config values.

Then read [CLI main](../../agentic_decomposer/cli.py#L144). This is where
`--system all` becomes four sequential runs.

## Entrypoint 2: YAML Configs

A normal MVP profile lives in [mvp_jpetstore.yaml](../../configs/mvp_jpetstore.yaml#L1).
That file records the system, model, evidence mode, candidate count, refinement
rounds, objective weights, and constraints.

Why YAML?

- It is easier to cite exact experiment profiles in a paper.
- It prevents long command lines from becoming accidental hidden state.
- It lets repeated runs vary only `seed` or ablation flags.

A config-only dry run should work:

```powershell
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --dry-run
```

## Entrypoint 3: Experiment Scripts

The experiment scripts are thin wrappers around the CLI. They exist so paper
experiments are repeatable:

- [run_mvp.py](../../experiments/run_mvp.py#L1): one system, usually JPetStore.
- [run_all_systems.py](../../experiments/run_all_systems.py#L1): all four systems.
- [run_ablation.py](../../experiments/run_ablation.py#L1): B0/A1/A2/A3 plus component ablations.

Open [run_ablation variants](../../experiments/run_ablation.py#L47). This is
where the experimental design becomes concrete variant names and CLI flags.

## Path Resolution Pattern

Open [paths.py constants](../../agentic_decomposer/paths.py#L31). The code uses
paths relative to the package file, not hard-coded Windows paths. That matters
for transfer to Linux.

Key ideas:

- `AGENTIC_ROOT` points at `agentic-experiments`.
- `FRAMEWORK_ROOT` points at `agentic-experiments/agentic_decomposer`.
- `CODEBASES_DIR` points at the four monolith folders.
- `GRAPH_ARTIFACTS_DIR` points at A6 graph JSON files.
- `METRICS_SCRIPT` points at `../src/metrics/scripts/evaluate_decomposition.py`.

Read [relative_to_agentic](../../agentic_decomposer/paths.py#L91). It makes
stored paths portable by writing forward-slash relative paths.

## Run Layout Pattern

Open [RunLayout](../../agentic_decomposer/runs.py#L17). This dataclass is the
canonical map of run folders and artifact paths.

A run folder looks like this:

```text
agentic_decomposer/runs/<run_id>/
  00_config/run_config.json
  01_evidence/evidence_pack.json
  02_domain/domain_model.json
  03_candidates/candidate_decompositions.json
  04_evaluation/evaluation_report.json
  05_refinement/refinement_patch.json
  06_final/final_output.json
  logs/llm_calls.jsonl
```

Why use a layout object instead of hard-coded strings in every agent?

- It avoids path drift between agents.
- It makes the run folder predictable for scripts.
- It makes adding a new artifact path local to one file.

## The First Full Trace

1. [CLI main](../../agentic_decomposer/cli.py#L144) chooses systems.
2. [CLI run one](../../agentic_decomposer/cli.py#L128) builds a `RunConfig` and a `ProcessController`.
3. [ProcessController init](../../agentic_decomposer/agents/process_controller.py#L35) creates a layout.
4. [ProcessController.run](../../agentic_decomposer/agents/process_controller.py#L41) executes stages.
5. [RunLayout.create](../../agentic_decomposer/runs.py#L67) makes folders.
