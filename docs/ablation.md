# Ablation experiments

The MVP must prove that the agentic components are **not decorative** — i.e.
each agent earns its place. This document describes the ablation grid run by
[`experiments/run_ablation.py`](../experiments/run_ablation.py).

---

## Ablation grid

Each variant is a single CLI invocation. The grid maps directly onto the
"Ablation table" outlined in the design brief.

| Variant ID | Evidence Constructor | Domain Agent | Generator        | Evaluator           | Refiner | Quality Gate | Flags                                                |
|------------|----------------------|--------------|------------------|---------------------|---------|--------------|------------------------------------------------------|
| `B0_single_shot` | (existing baseline) | no       | 1 candidate (old pipeline) | post-hoc scoring | no      | no           | reuse `results/<agent>/baseline-1/<repo>/decomposition.json` |
| `A1_gen_only` | yes                | yes          | 1 candidate      | post-hoc scoring    | no      | yes          | `--num-candidates 1 --no-refiner`                    |
| `A2_eval_select` | yes             | yes          | 3 candidates     | selects best        | no      | yes          | `--no-refiner`                                       |
| `A3_refined` | yes                 | yes          | 3 candidates     | selects best        | 1 round | yes          | (defaults)                                           |
| `A_no_domain` | yes               | no           | 3 candidates     | selects best        | 1 round | yes          | `--no-domain-agent`                                  |
| `A_no_qg`  | yes                  | yes          | 3 candidates     | metrics only        | 1 round | no           | `--no-quality-gate`                                  |
| `A_1cand_refined` | yes            | yes          | 1 candidate      | post-hoc scoring    | 1 round | yes          | `--num-candidates 1`                                 |

`B0_single_shot` is **not** re-run by the framework. It is loaded from the
existing `results/codex/baseline-1/<repo>/decomposition.json` (or whichever
agent family you choose as the reference single-shot baseline) and scored with
the same metric engine during real runs. In `--dry-run`, the row is pointer-only.

---

## How to run the grid

```powershell
# Core comparison plus component ablations on JPetStore, three repeated runs each, GPT-5.
python experiments/run_ablation.py `
  --system jpetstore-6 `
  --model gpt-5 `
  --runs 3
```

```powershell
# Same grid on all four systems (6 agentic variants x 4 systems x 3 runs = 72 agentic runs).
python experiments/run_ablation.py `
  --system all `
  --model gpt-5 `
  --runs 3
```

The script:

1. Reads the `B0` decomposition from `results/codex/baseline-1/<repo>/decomposition.json`.
   (Configurable via `--b0-agent` if you want claude-code instead.)
2. Scores `B0_single_shot` via the metric engine in real runs and records the row.
3. Runs each of the six `A*` variants `--runs` times.
4. Scores every produced decomposition.
5. Emits `experiments/results_ablation/<system>_<model>_<timestamp>.csv` with
   one row per (variant, run, system) and one row per metric.

## Expected pattern

Based on the previous paper's findings, the expected qualitative outcome is:

| Metric  | Expected direction (vs `B0`)           | Expected ablation effect                                  |
|---------|----------------------------------------|-----------------------------------------------------------|
| CiD     | unchanged or slightly higher           | removing the Refiner should hurt the most                 |
| CMod    | slight improvement                     | removing the Refiner should hurt                          |
| DI      | improvement                            | removing the Domain Agent should hurt the most            |
| BCP     | improvement                            | removing the Domain Agent should hurt the most            |
| TC      | unchanged                              | unaffected by any agent (needs git-history input — V1)    |
| MoJoFM  | unchanged or slight improvement        | uncertain; mostly driven by candidate diversity           |
| tokens  | substantially higher than `B0`         | proportional to (num_candidates × refinement_rounds)      |
| runtime | substantially higher than `B0`         | same                                                      |

The paper's claim is **not** "agentic beats everything"; it is "agentic gives
more controllable trade-offs and a clear ablation story". See
[architecture.md §1](architecture.md#1-why-this-framework-exists) for the framing.

Stability summaries, candidate-strategy win rates, refinement-effect deltas,
and quality-gate violation rollups are useful follow-on analyses, but they are
not emitted by the MVP script yet. They can be derived from the per-run folders
and the main ablation CSV after the Linux batch completes.
