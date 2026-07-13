# 07 - Experiments And Results

This chapter explains how the framework becomes a paper experiment. The code is
not just a tool; it is a controlled experimental harness.

## MVP Experiment Question

The first experiment should answer:

```text
Does the agentic generate/evaluate/refine loop improve over the previous
single-shot LLM decomposition, using the same systems and metric engine?
```

This is intentionally narrow. It is enough for the first result because it tests
the central claim of the new framework.

## Experiment Scripts

Open these files:

- [run_mvp.py](../../experiments/run_mvp.py#L1);
- [run_all_systems.py](../../experiments/run_all_systems.py#L1);
- [run_ablation.py](../../experiments/run_ablation.py#L1).

These are wrappers around the CLI. They do not implement a new pipeline. That is
a design choice: experiments should exercise the same framework path as normal
users.

## Single-System MVP

Use this first on Linux:

```bash
cd agentic-experiments
source .venv/bin/activate
python agentic_decomposer/experiments/run_mvp.py \
  --system jpetstore-6 \
  --model gpt-5 \
  --runs 1
```

The script defaults to the MVP shape:

```text
one system
one model
80k_concat
3 candidates
1 refinement round
```

JPetStore is the best first real target because it is small enough to debug and
has a familiar e-commerce domain.

## All-System Run

Open [run_all_systems main](../../experiments/run_all_systems.py#L36).

The script loops over:

```text
demo
jpetstore-6
spring-petclinic
PartsUnlimitedMRP
```

Run it after JPetStore works:

```bash
python agentic_decomposer/experiments/run_all_systems.py --model gpt-5
```

Do not jump to all four systems until one-system output is sensible. Debugging
one failing system is cheaper than untangling four failures at once.

## Ablation Study

Open [run_ablation variants](../../experiments/run_ablation.py#L47).

The core comparison rows are:

| Variant | Meaning |
|---------|---------|
| `B0_single_shot` | Old single-shot decomposition from `results/`, scored with the same metric engine. |
| `A1_gen_only` | One generated candidate, no refinement. |
| `A2_eval_select` | Three candidates, evaluator selects best, no refinement. |
| `A3_refined` | Three candidates, evaluator selects best, one refinement round. |

Component ablations are:

| Variant | Meaning |
|---------|---------|
| `A_no_domain` | Remove Domain Agent (placeholder) to test whether domain modeling matters. > **⚠️ TEMPORARY PLACEHOLDER — NOT CONCRETIZED.** The Domain Knowledge
> Extractor is a bare placeholder (single LLM call + prompt). Planned for
> proper development in V2. Treat as temporary scaffold. |
| `A_no_qg` | Remove Quality Gate effects to test governance value. |
| `A_1cand_refined` | Keep refinement but remove multi-candidate diversity. |

Run:

```bash
python agentic_decomposer/experiments/run_ablation.py \
  --system jpetstore-6 \
  --model gpt-5 \
  --runs 3
```

Then run all systems:

```bash
python agentic_decomposer/experiments/run_ablation.py \
  --system all \
  --model gpt-5 \
  --runs 3
```

## What The Ablation CSV Contains

Open [write rows](../../experiments/run_ablation.py#L168).

Each row contains:

```text
system
variant
run
status
run_id
final_output path
model
evidence mode
summarisation strategy
MoJoFM, CiD, CMod, BCP, DI, TC, LC, DTP, num_services
```

For `B0_single_shot`, the path points to an existing baseline decomposition. For
agentic variants, the path points to a generated `final_output.json`.

## How To Interpret Results

Do not ask only "did A3 beat B0?" Ask a more careful set of questions:

| Question | Compare |
|----------|---------|
| Does candidate diversity help? | `A1_gen_only` vs `A2_eval_select` |
| Does refinement help? | `A2_eval_select` vs `A3_refined` |
| Does domain modeling help? | `A3_refined` vs `A_no_domain` |
| Does quality governance help? | `A3_refined` vs `A_no_qg` |
| Does one candidate plus refinement suffice? | `A3_refined` vs `A_1cand_refined` |
| Does agentic beat old single-shot? | `B0_single_shot` vs `A3_refined` |

Expected pattern:

- CiD should remain high or improve.
- DI and BCP should improve if the Domain Agent helps (note: Domain Extractor is currently a placeholder).
- TC may not improve until repository-mining signals are added.
- Tokens and runtime will increase.
- MoJoFM may improve, but it is not guaranteed.

## Per-Run Artifacts To Inspect

For one run, open:

```text
agentic_decomposer/runs/A3_refined/jpetstore-6_gpt5_80kconcat_seed1/
```

Then inspect:

1. `01_evidence/evidence_pack.json`: did evidence look plausible?
2. `02_domain/domain_model.json` ⚠️ (placeholder): did capabilities make any sense?
3. `03_candidates/candidate_decompositions.json`: did strategies differ?
4. `04_evaluation/evaluation_report.json`: why did evaluator select the best?
5. `05_refinement/refinement_patch.json`: what changed?
6. `05_refinement/refined_evaluation_report.json`: did metrics improve?
7. `06_final/final_output.json`: what got published?

## Debugging Failed Runs

Use this order:

1. Check `logs/controller.log` for stage failure.
2. Check `logs/agent_<name>.log` for local agent failure.
3. Check `logs/llm_calls.jsonl` for raw LLM output.
4. Check `03_candidates/schema_validation.json` if the Generator produced bad JSON.
5. Check `04_evaluation/evaluation_report.json.metadata.engine_warnings` if metrics are null.

## No-API Practice Commands

Before a real Linux batch, these should pass:

```bash
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --dry-run
python -m agentic_decomposer run --config configs/mvp_all_systems.yaml --system all --dry-run
python agentic_decomposer/experiments/run_ablation.py --system demo --runs 1 --dry-run
```

## Checkpoint Questions

- Which comparison isolates candidate diversity?
- Which comparison isolates the Refiner?
- Which comparison isolates the Domain Agent? (Note: Domain Extractor is currently a placeholder.)
- Why should TC be interpreted cautiously in the MVP?
- Which artifact would you inspect to explain a metric regression after refinement?

## Mini Exercise

Design the first paper table from the ablation CSV:

```text
Rows: system x variant
Columns: MoJoFM, CiD, CMod, DI, BCP, TC, tokens, runtime
Group: B0, A1, A2, A3
```

Then design one diagnostic table:

```text
Rows: system
Columns: selected candidate strategy, pre-refinement score, post-refinement score, applied operations
```

If you can design both tables, you understand how experiment outputs connect to
the paper story.
