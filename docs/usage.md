# Usage

Practical command-line usage for `agentic_decomposer`. Mirror this on Linux —
all commands work unchanged once the workspace layout (`agentic-experiments/`
and `src/metrics/` side by side under a shared parent) is preserved.

---

## Install

```powershell
cd agentic-experiments
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r agentic_decomposer/requirements.txt
```

Then either install the package in editable mode:

```powershell
pip install -e agentic_decomposer
```

or set `PYTHONPATH=agentic_decomposer` before invoking `python -m agentic_decomposer`.

---

## API keys

LiteLLM picks the provider automatically from the model string. Set at least
the keys for the providers you intend to use.

```powershell
$env:OPENAI_API_KEY    = "sk-..."           # for gpt-5, gpt-4o, etc.
$env:ANTHROPIC_API_KEY = "sk-ant-..."       # for claude-sonnet-4, claude-opus, etc.
$env:GEMINI_API_KEY    = "..."              # for gemini/gemini-2.5-pro
```

On Linux:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
```

---

## Running a single system

```powershell
python -m agentic_decomposer run `
  --system jpetstore-6 `
  --model gpt-5 `
  --evidence-mode llm `
  --num-candidates 3 `
  --max-refinement-rounds 1
```

Valid `--system` values:

| Value               | Codebase folder                            |
|---------------------|--------------------------------------------|
| `demo`              | `codebases/demo`                           |
| `jpetstore-6`       | `codebases/jpetstore-6`                    |
| `spring-petclinic`  | `codebases/spring-petclinic`               |
| `PartsUnlimitedMRP` | `codebases/PartsUnlimitedMRP`              |
| `all`               | all four, executed sequentially            |

---

## Running all four systems

```powershell
python -m agentic_decomposer run --system all --model gpt-5
```

This is equivalent to four sequential single-system runs. Outputs land in
`agentic_decomposer/runs/<system>_<model>_<strategy>_<seed>/` per system.

---

## All command-line flags

| Flag                           | Default          | Description                                                                 |
|--------------------------------|------------------|-----------------------------------------------------------------------------|
| `--system`                     | required unless `--config` contains `system` | `demo` \| `jpetstore-6` \| `spring-petclinic` \| `PartsUnlimitedMRP` \| `all` |
| `--model`                      | `gpt-5`          | LiteLLM model string (e.g. `gpt-5`, `anthropic/claude-sonnet-4-20250514`)     |
| `--evidence-mode`              | `llm`            | `llm` \| `deterministic` \| `external` — see [evidence_modes.md](evidence_modes.md) |
| `--external-views-dir`         | — (required when `external`) | Folder containing pre-existing `A1.md`..`A5.md` per system           |
| `--summarisation-strategy`     | `80k_concat`     | `30k_concat` \| `30k_aggregate` \| `50k_concat` \| `50k_aggregate` \| `80k_concat` \| `80k_aggregate` \| `hierarchical` |
| `--num-candidates`             | `3`              | Number of candidate decompositions per run                                  |
| `--max-refinement-rounds`      | `1`              | Set to `0` to disable refinement (ablation mode)                            |
| `--no-domain-agent`            | off              | Ablation flag — skip Domain Extractor; downstream agents see empty model    |
| `--no-quality-gate`            | off              | Ablation flag — skip standalone Quality Gate and evaluator quality penalties |
| `--no-refiner`                 | off              | Ablation flag — same as `--max-refinement-rounds 0`                          |
| `--seed`                       | `1`              | Run seed; appears in `run_id` to keep repeated runs distinct                 |
| `--config`                     | —                | Path to a YAML config file; CLI flags override values in the file           |
| `--runs-dir`                   | `agentic_decomposer/runs/` | Output directory (one folder per run is created inside)             |
| `--dry-run`                    | off              | Validate config, create empty run folder, and exit                          |

---

## Config files

YAML config files in [`configs/`](../configs/) capture standard run profiles:

```yaml
# configs/mvp_jpetstore.yaml
system: jpetstore-6
model: gpt-5
evidence_mode: llm
summarisation_strategy: 80k_concat
num_candidates: 3
max_refinement_rounds: 1
objectives:
  structural_modularity: 0.30
  domain_alignment: 0.30
  cyclic_independence: 0.20
  migration_feasibility: 0.20
constraints:
  each_class_assigned_once: true
  allow_unassigned_classes: false
  max_services: null
  min_services: 2
seed: 1
```

Use them like:

```powershell
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --seed 2  # override
```

From the repository root, both `configs/mvp_jpetstore.yaml` and
`agentic_decomposer/configs/mvp_jpetstore.yaml` resolve to the framework config
folder.

---

## Outputs

Every run produces a self-contained folder under `agentic_decomposer/runs/`:

```
agentic_decomposer/runs/jpetstore-6_gpt5_80kconcat_seed1/
  00_config/        run_config.json
  01_evidence/      evidence_pack.json + supporting files
  02_domain/        domain_model.json
  03_candidates/    candidate_decompositions.json
  04_evaluation/    evaluation_report.json + ranking
  05_refinement/    refinement_patch.json + refined artefacts
  06_final/         final_output.json + decomposition.json (B0-compatible shape)
  logs/             controller.log, agent_*.log, llm_calls.jsonl
```

The file `06_final/decomposition.json` has the same shape as the existing
`results/<agent>/baseline-X/<repo>/decomposition.json` files, so it can be
scored directly by the existing metric engine.

---

## Reproducibility tips

- Pin a model and a seed in the config file; record both in the run folder.
- Don't edit prompts during an experiment batch. Prompt files are versioned in
  [`prompts/`](../prompts/) and the run metadata records the framework version.
- Don't edit a codebase between runs. The framework uses
  `codebases/<system>/` as-is; pinning is done by your git checkout, not by
  the framework.
- LLM nondeterminism: same model + same seed will still vary slightly. For
  publishable numbers, do `n >= 3` repeated runs and report mean ± std (see
  [scripts/calculate_metrics_paper_comparison.py](../../scripts/calculate_metrics_paper_comparison.py) for the existing pattern).
