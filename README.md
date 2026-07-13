# agentic_decomposer

A multi-agent framework for monolith-to-microservices decomposition.

Built on top of the four monolith codebases and metric engine already used in the
single-shot LLM decomposition paper. This package adds **specialised agents** with
**explicit JSON artifact contracts** and an **evaluate→refine feedback loop**.

The motivation, full agent spec, and experimental roadmap are written up in detail
under [docs/](docs/). New readers should start with the guided onboarding track:
[docs/learning/README.md](docs/learning/README.md).

---

## TL;DR — what this framework does

```
Monolith repo (pinned SHA)
   │
   ▼
[Process Controller] ──────► run_config.json
   │
   ▼
[Architectural Evidence Constructor] ──► evidence_pack.json   (A1..A5 + A6)
   │
   ▼
[Domain Knowledge Extractor]          ──► domain_model.json  ⚠️  (placeholder — not yet concretized)
   │
   ▼
[Decomposition Generator]             ──► candidate_decompositions.json  (3 strategies)
   │
   ▼
[Decomposition Evaluator]             ──► evaluation_report.json
[Quality Gate]                        ──► quality_gate_report.json
   │
   ▼
[Decomposition Refiner]               ──► refinement_patch.json + refined_candidate.json
   │
   ▼
[Decomposition Evaluator] (re-score)  ──► refined_evaluation_report.json
   │
   ▼
[Process Controller] selects best     ──► final_output.json
                                          decomposition.json
```

Every arrow is a JSON file. Every agent has a strict input/output contract validated
against the schemas in [schemas/](schemas/).

---

## Repository layout

```
agentic_decomposer/
├── README.md                        ← you are here
├── pyproject.toml                   ← package metadata
├── requirements.txt                 ← pinned runtime deps
├── docs/                            ← architecture, usage, schemas, ablation, ...
├── agentic_decomposer/              ← python package (the framework)
│   ├── cli.py                       ← `python -m agentic_decomposer ...`
│   ├── config.py                    ← RunConfig loader
│   ├── paths.py                     ← workspace path resolver (relative, cross-platform)
│   ├── logger.py                    ← structured logging
│   ├── llm/                         ← LiteLLM client + token counting + retries
│   ├── agents/                      ← Process Controller + 6 specialised agents
│   ├── artifacts/                   ← schema registry, validators, ID minting
│   ├── evidence/                    ← A1..A6 builders (llm / deterministic / external)
│   ├── metrics/                     ← metric engine subprocess wrapper + quality gate
│   └── refinement/                  ← patch operations + applier
├── schemas/                         ← 7 JSON Schemas (artifact contracts)
├── prompts/                         ← prompt templates per agent / strategy
├── configs/                         ← YAML run configs (default, ablation variants)
├── experiments/                     ← driver scripts for the MVP RQs
└── runs/                            ← per-run output folders (gitignored)
```

---

## Quick start (after the agents are implemented in later commits)

```powershell
# Install deps
cd agentic-experiments
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r agentic_decomposer/requirements.txt

# Set your LLM provider keys (any one is enough — LiteLLM picks the right one)
$env:OPENAI_API_KEY    = "sk-..."
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:GEMINI_API_KEY    = "..."

# Run the MVP on JPetStore only
python -m agentic_decomposer run `
  --system jpetstore-6 `
  --model gpt-5 `
  --evidence-mode llm `
  --num-candidates 3 `
  --max-refinement-rounds 1

# Run on all four systems
python -m agentic_decomposer run --system all --model gpt-5

# Reproduce the RQ2 ablation grid
python experiments/run_ablation.py --system jpetstore-6 --model gpt-5
```

On Linux the same commands run unchanged. The framework resolves paths relative
to the workspace root, so `../src/metrics/scripts/evaluate_decomposition.py` is
located the same way it is in [scripts/calculate_metrics_paper_comparison.py](../scripts/calculate_metrics_paper_comparison.py).

---

## Where each prior-paper input is reused

| Old paper artifact                          | Reused here as                                                 |
| ------------------------------------------- | -------------------------------------------------------------- |
| Pinned monolith codebases                   | [codebases/](../codebases/) (read-only input)                  |
| Static class dependency graph (A6)          | [graph-artifacts/](../graph-artifacts/) (Evidence Constructor) |
| Decomposition JSON schema (`{tool:{decomposition:{...}}}`) | Candidate schema is a superset (adds `evidence_refs`, `rationale`) |
| Metric engine (Java + Python)               | `../src/metrics/scripts/evaluate_decomposition.py` via subprocess |
| Single-shot baseline                        | The `B0` reference in every comparison table                   |
| Reference SRMs                              | Used by the metric engine for MoJoFM                            |

See [docs/learning/README.md](docs/learning/README.md) for the full read-along
curriculum, or [docs/architecture.md](docs/architecture.md) for the concise
architecture reference.
