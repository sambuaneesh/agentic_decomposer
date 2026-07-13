# Architecture

This document is the canonical description of the framework's agents, artifacts,
control flow, and design rules. If anything in the code disagrees with this
document, the document is right and the code is a bug.

---

## 1. Why this framework exists

The previous single-shot LLM decomposition pipeline produced **structurally clean,
low-cycle decompositions** but **weakly recovered reference, domain, and team
boundaries**. Concretely:

| Metric  | Old single-shot LLM mean | SOTA tool mean |
|---------|-------------------------:|---------------:|
| CiD     | 87.83                    | 65.11          |
| MoJoFM  | 27.33                    | 51.41          |
| DI      | 24.14                    | 34.84          |
| TC      | 20.16                    | 31.19          |

This framework asks one focused question:

> Does an agentic generate → evaluate → refine loop, with a dedicated domain
> agent and a quality gate, improve over the previous single-shot pipeline,
> using the same input artifacts and the same metric engine?

It is **not** "LLMs writing microservice code". It is architecture-level
exploratory decomposition with specialised agents.

---

## 2. Agents and their classifications

The diagram uses three agent types: **Tool** (deterministic), **Hybrid** (tool +
LLM), and **LLM** (mainly generative).

| Agent                                  | Type   | Responsibility                                                                       |
|----------------------------------------|--------|---------------------------------------------------------------------------------------|
| Process Controller                     | Tool   | Sequences agents, manages iterations, selects final candidate, logs everything.       |
| Architectural Evidence Constructor     | Hybrid | Produces `evidence_pack.json` (A1..A5 from LLM/deterministic, A6 from static graph).  |
| Domain Knowledge Extractor             | Hybrid | Produces `domain_model.json` with business capabilities + class-capability matrix. > **⚠️ TEMPORARY PLACEHOLDER — NOT CONCRETIZED.** The Domain Knowledge
> Extractor is a bare placeholder (single LLM call + prompt). Planned for
> proper development in V2. Treat as temporary scaffold.   |
| Decomposition Generator                | LLM    | Produces ≥1 candidate decomposition per strategy (dependency / domain / balanced).    |
| Decomposition Evaluator                | Tool   | Runs the existing metric engine and quality-gate; produces `evaluation_report.json`.  |
| Quality Gate (MVP) → Quality Governance (V3) | Tool/Hybrid | Schema + structural checks now; stakeholder constraints later.                   |
| Decomposition Refiner                  | Hybrid | Applies controlled patch operations to repair the best candidate.                     |

---

## 3. Artifact flow

Every arrow in the diagram is a JSON file on disk. There is no shared memory and
no agent-to-agent function call without a file handoff. This makes the system
debuggable, ablatable, and reproducible.

```
                       ┌───────────────────────────┐
   run_config.yaml ──► │     Process Controller    │
                       └─────────────┬─────────────┘
                                     │ writes run_config.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Evidence Constructor     │ ◄── codebases/<system>/
                       │  (A1..A5 + A6)            │ ◄── graph-artifacts/<system>-class-dependency.json
                       └─────────────┬─────────────┘
                                     │ evidence_pack.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Domain Extractor         │  ⚠️ Placeholder — see Stage 4 in mvp_roadmap.md

                       └─────────────┬─────────────┘
                                     │ domain_model.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Generator (×3 strategies)│
                       └─────────────┬─────────────┘
                                     │ candidate_decompositions.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Evaluator + Quality Gate │ ◄── ../src/metrics/scripts/evaluate_decomposition.py
                       └─────────────┬─────────────┘
                                     │ evaluation_report.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Refiner (≤N rounds)      │
                       └─────────────┬─────────────┘
                                     │ refinement_patch.json + refined_candidate.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Evaluator (re-score)     │
                       └─────────────┬─────────────┘
                                     │ refined_evaluation_report.json
                                     ▼
                       ┌───────────────────────────┐
                       │  Process Controller       │
                       │  selects + reports        │
                       └─────────────┬─────────────┘
                                     │ final_output.json
                                     ▼ decomposition.json   ← schema-compatible with B0
```

---

## 4. Run-folder layout

One directory per run; everything written into it. Reproducibility property:
deleting `agentic_decomposer/runs/<run_id>/` and re-running with the same config and the same model
seed should reproduce results modulo LLM nondeterminism.

```
agentic_decomposer/runs/<run_id>/
  00_config/
    run_config.json
  01_evidence/
    evidence_pack.json
    raw_llm_views.json            (only when --evidence-mode llm)
    deterministic_views.json      (only when --evidence-mode deterministic)
  02_domain/
    domain_model.json
    class_capability_matrix.csv
  03_candidates/
    candidate_decompositions.json
    schema_validation.json
  04_evaluation/
    evaluation_report.json
    quality_gate_report.json
    candidate_ranking.csv
  05_refinement/
    refinement_patch.json
    refined_candidate.json
    refined_evaluation_report.json
  06_final/
    final_output.json
    decomposition.json            ← same shape as results/<agent>/baseline-X/<repo>/decomposition.json
  logs/
    controller.log
    agent_<name>.log              (one per agent invocation)
    llm_calls.jsonl               (every prompt + response + token count)
```

---

## 5. Design rules

1. **No agent-to-agent state outside JSON files.** This is what makes ablation
   experiments cleanly definable (`--no-domain-agent` literally skips the domain
   step and the generator gets an empty `domain_model.json`).
2. **Schemas are normative.** Every artifact is validated against
   [../schemas/](../schemas/) before it is written and again before it is read.
3. **Evidence IDs are stable within a run.** `C001`, `BC001`, `API_001`, etc. are
   minted in the Evidence Constructor and referenced by every downstream agent.
4. **The Refiner edits, it does not regenerate.** Patches use a small fixed set
   of operations; full rewrites are reserved for catastrophic schema failures.
5. **The Evaluator is the metric authority.** Composite scores are for the
   Controller's selection decisions only; published results use the individual
   Wang metrics straight from the metric engine.
6. **The MVP Quality Gate is rule-based.** The future Quality Governance Agent
   (stakeholder constraints, regulatory rules) is explicitly out of scope for V1.
7. **Paths are workspace-relative.** Resolution uses
   `Path(__file__).resolve().parents[N]` so the framework runs identically on
   Windows and Linux as long as the `agentic-experiments/` and `src/metrics/`
   layout is preserved.

---

## 6. Mapping to the previous paper

The new framework reuses every Phase-1 / Phase-2 / Phase-3 input artifact:

| Old paper artifact                        | New framework consumer                       |
|-------------------------------------------|----------------------------------------------|
| Phase 1 repo summaries                    | Evidence Constructor (LLM mode input)        |
| Phase 2 A1 component diagram              | Evidence Constructor (external mode input)   |
| Phase 2 A2 component overview table       | Evidence Constructor (external mode input)   |
| Phase 2 A3 API endpoints                  | Evidence Constructor                         |
| Phase 2 A4 technology map                 | Evidence Constructor                         |
| Phase 2 A5 dynamic interactions           | Evidence Constructor                         |
| Phase 2 A6 dependency / call graph        | Evidence Constructor (always, deterministic) |
| Phase 3 decomposition JSON schema         | Candidate decomposition (superset)           |
| Reference SRMs                            | Metric engine (MoJoFM)                       |
| Wang metric engine                        | Decomposition Evaluator                      |

See [evidence_modes.md](evidence_modes.md) for how A1..A5 are obtained in each of
the three supported modes.

---

## 7. What this framework deliberately is not

- It is not a LangGraph / CrewAI / AutoGen application. A deterministic Python
  orchestrator was chosen for reproducibility and paper defensibility. The
  framework is "agentic" because of specialised responsibilities + JSON
  contracts + evaluator-refiner feedback, not because of a flashy library.
- It is not a code-migration tool. It outputs a candidate service partition.
  Producing the actual microservice code is out of scope.
- It is not interactive (yet). Human-in-the-loop refinement is the V3 milestone;
  the MVP is fully automated.
- It is not a metric framework. It calls the existing metric engine; it does
  not re-implement Wang et al.'s scoring.
