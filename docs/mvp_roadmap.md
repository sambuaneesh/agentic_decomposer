# MVP roadmap

Status board for the staged build of `agentic_decomposer/`. Update this file
after every stage so the user always knows what works end-to-end and what is
still a stub.

Legend: `[x]` done · `[~]` partial · `[ ]` not started.

---

## Stage 0 — Scaffold

- [x] Package directory structure (`agentic_decomposer/`, `agents/`, `llm/`, `evidence/`, `metrics/`, `refinement/`, `artifacts/`, `runs/`)
- [x] `requirements.txt` and `pyproject.toml`
- [x] Top-level [`README.md`](../README.md) with quick start
- [x] Docs scaffold: `architecture.md`, `usage.md`, `evidence_modes.md`, `schemas.md`, `metric_engine.md`, `ablation.md`, `mvp_roadmap.md` (this file)
- [x] `.gitignore` additions for `runs/`, `.venv/`, and generated experiment result folders

## Stage 1 — Artifact schemas

- [x] `run_config.schema.json`
- [x] `evidence_pack.schema.json`
- [x] `domain_model.schema.json`
- [x] `candidate_decomposition.schema.json`
- [x] `evaluation_report.schema.json`
- [x] `refinement_patch.schema.json`
- [x] `final_output.schema.json`
- [x] Schema registry + validator helpers in `artifacts/`

## Stage 2 — Process Controller + CLI

- [x] `paths.py` — workspace path resolver
- [x] `config.py` — RunConfig loader (YAML → typed object → validated JSON)
- [x] `logger.py` — structured logging with per-agent log files
- [x] `agents/base.py` — `BaseAgent` ABC
- [x] Stub implementations for all 6 agents that produce schema-valid placeholder JSON
- [x] `agents/process_controller.py` — orchestrates the full sequence
- [x] `cli.py` — `python -m agentic_decomposer run …`
- [x] End-to-end "dry run" that produces a full `runs/<run_id>/` tree with valid placeholders

## Stage 3 — Architectural Evidence Constructor

- [x] `evidence/source_walker.py` — walks Java sources, builds class inventory
- [x] `evidence/dependency_graph_loader.py` — loads A6 from `graph-artifacts/`
- [x] `evidence/llm_views.py` — generates A1..A5 via LLM
- [x] `evidence/deterministic_views.py` — derives A2/A3/A4 from source statically
- [x] `evidence/external_views.py` — loads pre-existing A1..A5 files
- [x] `agents/evidence_constructor.py` — wires the chosen mode, mints stable IDs, normalises to `evidence_pack.json`

## Stage 4 — Domain Knowledge Extractor

- [x] `prompts/domain_extractor.md`
- [x] `agents/domain_extractor.py` — LLM call with evidence-ID citation enforcement
- [x] Emit `class_capability_matrix.csv`

## Stage 5 — Multi-candidate Generator

- [x] `prompts/generator_dependency_first.md`
- [x] `prompts/generator_domain_first.md`
- [x] `prompts/generator_balanced.md`
- [x] `agents/decomposition_generator.py` — N candidates, schema validation, rationale + evidence_refs enforcement

## Stage 6 — Evaluator + Quality Gate

- [x] `metrics/quality_gate.py` — local structural checks (every class assigned, no duplicates, no empty services, ...)
- [x] `metrics/engine.py` — subprocess wrapper for `../src/metrics/scripts/evaluate_decomposition.py`
- [x] `metrics/composite_score.py` — weighted score for controller-internal candidate selection
- [x] `agents/decomposition_evaluator.py`
- [x] `agents/quality_gate.py`

## Stage 7 — Refiner

- [x] `refinement/operations.py` — dataclasses for `move_class`, `split_service`, `merge_services`, `rename_service`, `add_dependency`, `remove_invalid_dependency`, `reassign_responsibility`
- [x] `refinement/patcher.py` — deterministic application of operations to a candidate
- [x] `prompts/refiner.md`
- [x] `agents/decomposition_refiner.py`

## Stage 8 — MVP experiment harness

- [x] `experiments/run_mvp.py` — single-system runner (default: jpetstore-6)
- [x] `experiments/run_all_systems.py` — all four monoliths
- [x] `experiments/run_ablation.py` — toggles `--no-domain-agent`, `--no-refiner`, `--no-quality-gate`, `--num-candidates 1`
- [x] `configs/mvp_jpetstore.yaml`, `configs/mvp_all_systems.yaml`, `configs/ablation/*.yaml`
- [x] Per-run results CSV builder (rows = system x variant, including B0 scoring rows in real runs)

---

## Static verification performed

- [x] `python -m compileall -q agentic_decomposer\agentic_decomposer agentic_decomposer\experiments`
- [x] `python -m agentic_decomposer run --system all --model gpt-5 --dry-run`
- [x] `python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --dry-run`
- [x] `python -m agentic_decomposer run --config configs/mvp_all_systems.yaml --system all --dry-run`
- [x] Deterministic Evidence Constructor smoke test on all four systems without API calls
- [x] Evaluator/Quality Gate smoke test with metric engine disabled, including evidence-ref validation and `--no-quality-gate` ablation behavior
- [x] `experiments/run_mvp.py --system demo --dry-run`
- [x] `experiments/run_all_systems.py --dry-run`
- [x] `experiments/run_ablation.py --system demo --runs 1 --dry-run`

The LLM-backed full pipeline is intentionally not executed in this Windows
validation pass; it is wired for execution on the target Linux machine with the
required LiteLLM credentials and the parent metric engine available at
`../src/metrics/scripts/evaluate_decomposition.py`.

---

## Definition of done for the MVP

The MVP is complete when:

1. A single command runs the full pipeline on JPetStore end-to-end.
2. The same command with `--system all` runs on all four monoliths.
3. The ablation harness produces a comparison table covering: B0 (old
   single-shot baseline reused from `results/`), A1 (agentic, no refinement),
   A2 (agentic + evaluator selection), A3 (agentic + 1 refinement round).
4. Every artifact validates against its schema.
5. Every metric in `evaluation_report.json` is sourced from the existing metric
   engine — no Python re-implementation of Wang metrics.
6. Documentation in [usage.md](usage.md), [evidence_modes.md](evidence_modes.md),
   [metric_engine.md](metric_engine.md), and [ablation.md](ablation.md) matches
   the implemented behaviour.
