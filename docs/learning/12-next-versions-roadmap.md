# 12 - Next Versions After Initial Testing

This document starts after the first real Linux run of the MVP. It answers a
practical research question:

```text
Once the framework runs end-to-end, what should we do next, what could we do
later, and how do we decide without losing the scientific thread?
```

Use this as the roadmap for V1, V2, V3, and beyond. The MVP already builds the
basic multi-agent loop. The next versions should turn that loop into a stronger
research instrument: more reliable, more measurable, more explainable, and more
convincing for a paper.

For a literature-grounded check of whether these versions are ambitious enough,
read [13-literature-gap-analysis.md](13-literature-gap-analysis.md) after this
roadmap.

Citation keys such as `[DataCentric2022]` and `[MOO2024]` are defined in the
[References](13-literature-gap-analysis.md#references) section of the literature
gap analysis. They are included here only where roadmap items are explicitly
motivated by the literature scan.

## The Big Rule

Do not add clever new agents immediately after the first successful run.

First, prove that the current pipeline runs, produces inspectable artifacts,
fails in understandable ways, and gives repeatable enough results to interpret.
Only then expand the architecture.

The order is:

```text
initial Linux test
  -> stabilize and audit
  -> establish result baselines
  -> analyze failure modes
  -> choose targeted V1 improvements
  -> run controlled comparisons
  -> only then add V2/V3 research extensions
```

## Version Labels

Use these labels consistently in notes, run IDs, result CSVs, and paper drafts.

| Label | Meaning | Main Question |
|-------|---------|---------------|
| MVP | Current implemented framework. | Does the agentic pipeline run end-to-end and produce valid artifacts? |
| V1 | Stabilized research baseline. | Can we trust the produced results enough to compare variants? |
| V2 | Stronger evidence and domain grounding. | Does richer architectural evidence improve decomposition quality? |
| V3 | Smarter agentic search and governance. | Do iterative, critic-style, or committee-style agents improve results? |
| V4 | Human-in-the-loop and workbench version. | Can an architect inspect, steer, and learn from the decomposition process? |
| V5 | Publication and replication package. | Can another researcher reproduce the study and understand the contribution? |

## What Counts As Initial Testing

Initial testing is not one command succeeding. Initial testing is the first
small batch of real runs that proves the MVP can produce meaningful artifacts.

Minimum initial test set:

| Test | Purpose | Must Inspect |
|------|---------|--------------|
| One JPetStore MVP run | First realistic end-to-end check. | Every artifact in the run folder. |
| One deterministic dry run | Confirms no-API path still works. | `evidence_pack.json`, `final_output.json`. |
| One ablation run on one system | Confirms variant orchestration. | CSV rows and variant run folders. |
| One all-system dry run | Confirms path mapping for all systems. | Per-system folders and logs. |
| One all-system real run, if budget allows | Confirms framework scales beyond JPetStore. | Null metrics, failed candidates, cost logs. |

Recommended first Linux command sequence:

```bash
cd ~/agentic-experiments
python -m venv .venv
source .venv/bin/activate
pip install -e agentic_decomposer
pip install -r agentic_decomposer/requirements.txt
export PYTHONPATH="$(pwd)/agentic_decomposer"

python -m compileall -q agentic_decomposer/agentic_decomposer agentic_decomposer/experiments
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --dry-run
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --run-id mvp_jpetstore_real_001
python agentic_decomposer/experiments/run_ablation.py --system jpetstore-6 --runs 1
```

Set provider credentials in the shell before real LLM runs. Do not put API keys
in config files or committed files.

## Initial Run Folder Inspection

After the first real run, open the run folder before looking at aggregate
metrics. A good result table is not useful if the artifacts are confused.

Inspect in this order:

1. `run_config.json`
2. `logs/llm_calls.jsonl`
3. `evidence/evidence_pack.json`
4. `domain/domain_model.json`
5. `candidates/candidate_decompositions.json`
6. `evaluation/evaluation_report.json`
7. `evaluation/quality_gate_report.json`
8. `refinement/refinement_patch.json`
9. `refinement/refined_candidate.json`
10. `evaluation/refined_evaluation_report.json`
11. `final/final_output.json`
12. `final/decomposition.json`

For each artifact, ask:

| Question | Why It Matters |
|----------|----------------|
| Is the JSON schema-valid? | Invalid artifacts make later results meaningless. |
| Are IDs stable and cited correctly? | Evidence grounding depends on references. |
| Are all classes assigned exactly once? | Service partitions must be complete. |
| Are service names meaningful and unique? | Empty or duplicate abstractions signal shallow output. |
| Are dependencies plausible? | Dependency shape affects cyclicity and coupling metrics. |
| Did the Refiner improve or damage the candidate? | The controller should not blindly prefer refinement. |
| Are metric values present or null with warnings? | Null metrics must be explained, not silently accepted. |
| Does the rationale cite actual evidence? | This is the core distinction from free-form LLM output. |

## Initial Result Decision Tree

Use this decision tree before building the next version.

```text
Did the real run crash?
  yes -> classify crash, fix V1 reliability, rerun same command
  no  -> continue

Are metrics null?
  yes -> debug metric engine integration before research claims
  no  -> continue

Are candidate artifacts schema-valid?
  no  -> fix parsing, schema, or prompt contract before adding features
  yes -> continue

Does the Quality Gate find severe grounding errors?
  yes -> classify failure modes, improve prompts/gates/refiner locally
  no  -> continue

Does refinement usually improve selected candidate?
  no  -> tune/refactor refinement before adding bigger agents
  yes -> continue

Are results stable across repeated runs?
  no  -> add repetitions, cost controls, variance reporting
  yes -> start V2 evidence expansion
```

## V1 - Stabilized Research Baseline

V1 is the first version after the MVP. It should make the framework trustworthy,
not bigger.

### V1 Goals

V1 should answer:

- Can the framework run on all benchmark systems without manual intervention?
- Are all failures classified and recoverable or clearly reported?
- Are metrics, quality gates, and final selections reproducible enough to study?
- Do the ablation variants directly support the research argument?
- Can a paper table be generated from run outputs without hand editing?

### V1 Must-Have Work

| Work | Why | Likely Files |
|------|-----|--------------|
| Add run result aggregation script | Paper tables need consistent rows. | `experiments/`, `runs.py`, docs. |
| Add failed-run classifier | Crashes, null metrics, schema errors, and LLM parse errors should be separated. | `agents/base.py`, `logger.py`, `llm/client.py`. |
| Add retry and backoff around LLM calls | Real APIs fail transiently. | `llm/client.py`. |
| Add cost/token summary per run | Agentic systems need cost reporting. | `llm/client.py`, final output schema. |
| Add automated artifact audit command | One command should inspect a run folder. | new script under `experiments/` or package CLI. |
| Add repeated-run support to MVP/all-system scripts | LLM variance matters. | `experiments/run_mvp.py`, `run_all_systems.py`. |
| Add plots or table generator | Avoid manual spreadsheet work. | `experiments/`, maybe `docs/results/`. |
| Add tests for patcher and quality gate | These are deterministic and high-value. | `tests/`, `metrics/quality_gate.py`, `refinement/patcher.py`. |
| Add Linux setup checklist result log | Record exact installed versions and paths. | docs and run metadata. |

### V1 Should-Have Work

| Work | Reason |
|------|--------|
| Store model name, provider, temperature, max tokens, and prompt file versions in `final_output.json`. | Makes runs auditable. |
| Add a run manifest with environment details. | Helps reproduce Linux results. |
| Add schema version fields to artifacts. | Future migrations become safer. |
| Add optional `--fail-fast` and `--continue-on-error` modes. | Useful for batch experiments. |
| Add candidate diversity diagnostics. | Detects when N candidates are essentially the same. |
| Add service-size distribution diagnostics. | Detects one huge service plus tiny leftovers. |
| Add evidence-coverage score. | Measures how much of the candidate rationale is grounded. |

### V1 Could-Have Work

These are useful but should not block baseline experiments:

- local cache for repeated LLM calls during prompt debugging;
- richer HTML run report;
- prompt snapshot copying into each run folder;
- structured log viewer;
- optional parallel execution for independent systems;
- CI job for compile, dry-run, schema validation, and docs link validation.

### V1 Acceptance Criteria

Call V1 done when all are true:

1. All four systems run with the same command family.
2. Each system has at least three repeated real runs for the main variant.
3. The ablation script produces B0, A1, A2, A3, and component ablation rows.
4. Every null metric has a recorded warning or failure reason.
5. Every failed candidate has a classified failure type.
6. Token/cost summary exists per run and per variant.
7. A table can be generated directly from run artifacts.
8. Documentation explains how to reproduce the table.

## V1 Analysis Checklist

After V1 experiments, build a result matrix with these columns:

| Column | Meaning |
|--------|---------|
| system | Benchmark system name. |
| run_id | Unique run folder. |
| variant | B0, A1, A2, A3, or ablation variant. |
| model | LLM model used. |
| evidence_mode | `llm`, `deterministic`, or `external`. |
| num_candidates | Candidate count. |
| refinement_rounds | Number of refinement rounds. |
| MoJoFM | Reference-boundary similarity. |
| CiD | Cyclic dependency score. |
| CMod | Modularity score. |
| BCP | Business-context purity. |
| DI | Distribution index. |
| TC | Topic cohesion. |
| LC | Logical cohesion. |
| DTP | Data type purity. |
| num_services | Service count. |
| composite_score | Internal selection score. |
| quality_passed | Local quality outcome. |
| violation_count | Count of quality violations. |
| token_total | Total tokens used. |
| estimated_cost | Provider cost if available. |
| failure_type | Empty if success. |

Then answer these questions:

1. Does A3 beat A1 on structural metrics more often than not?
2. Does A3 recover reference boundaries better than B0, or only improve
   structural cleanliness?
3. Does the Domain Agent improve BCP, TC, LC, or DTP?
4. Does the Quality Gate reduce invalid candidates or merely penalize them after
   generation?
5. Does the Refiner improve metrics, quality violations, both, or neither?
6. Are improvements consistent across systems or concentrated in one codebase?
7. Are gains worth the extra token cost?
8. Are failures due to prompts, evidence extraction, metric engine issues, or
   genuine ambiguity in the monolith?

## V2 - Stronger Evidence And Domain Grounding

V2 should improve what the agents know before they generate services.

The old paper's limitation was that LLMs could produce structurally clean
partitions without reliably matching reference boundaries. V2 should test
whether richer evidence helps recover those boundaries.

### V2 Evidence Extensions

| Extension | What It Adds | Why It Might Matter |
|-----------|--------------|---------------------|
| Database/table ownership evidence `[DataCentric2022]` | Tables, repositories, entities, and data access paths. | Helps service data ownership and DTP. |
| Knowledge-graph/semantic evidence `[KG2022]` `[SemanticReview2025]` | Typed relations among classes, APIs, data, capabilities, and vocabulary. | Makes evidence queryable and aligns with semantic decomposition work. |
| Repository co-change evidence `[OfflineMining2022]` | Classes that change together across commits. | Adds repository-mining/evolutionary signal beyond static source structure. |
| Runtime or endpoint trace evidence `[Dynamic2024]` `[StaticDynamic2020]` | Which classes participate in user flows. | Helps recover use-case-oriented boundaries. |
| Test coverage evidence | Test packages and integration tests around features. | Reveals domain slices not obvious from packages. |
| API-flow evidence | Controller -> service -> repository paths. | Grounds endpoints in implementation flows. |
| Method-level dependencies | Finer graph than class-level edges. | Can reduce noisy class-level dependency decisions. |
| Build/module metadata | Gradle/Maven modules, packages, dependencies. | Adds architectural hints already present in code. |
| Text-topic embeddings `[SemanticReview2025]` | Topic similarity of class names, comments, methods. | Can support TC/LC-style reasoning. |

### V2 Implementation Pattern

Do not bolt evidence directly into prompts. Follow the artifact pattern:

```text
extract raw signal
  -> normalize into evidence_pack or a new schema-backed artifact
  -> validate
  -> cite with stable IDs
  -> expose compact context to agents
  -> add ablation switch
  -> evaluate impact
```

For each new evidence type, define:

| Decision | Example |
|----------|---------|
| Raw source | Git history, SQL mappings, runtime traces, tests. |
| Extractor | New module under `evidence/`. |
| Artifact fields | Add to `evidence_pack` or create a separate artifact. |
| ID prefix | Example: `CO_001`, `DB_001`, `TR_001`. |
| Prompt exposure | Compact table, not raw dump. |
| Quality checks | Verify cited IDs and source consistency. |
| Ablation | `A_no_cochange`, `A_no_data`, etc. |
| Expected metric effect | Which Wang metrics should improve? |

### V2 Concrete Build Order

Build V2 in this order, using the literature scan as the rationale for the
first four items:

1. Database/entity ownership evidence `[DataCentric2022]`.
2. Knowledge-graph or semantic evidence representation `[KG2022]`
  `[SemanticReview2025]`.
3. Repository co-change/mining evidence `[OfflineMining2022]`.
4. Optional runtime traces `[Dynamic2024]` `[StaticDynamic2020]`.
5. API-flow evidence.
6. Method-level dependency graph.
7. Topic embeddings or semantic clustering `[SemanticReview2025]`.

Reasoning:

- Data ownership is central to microservice decomposition `[DataCentric2022]`.
- Knowledge-graph/semantic evidence aligns the framework with recent semantic
  and graph-based extraction work `[KG2022]` `[SemanticReview2025]`.
- Co-change is usually available without instrumenting applications and is a
  repository-mining style signal `[OfflineMining2022]`.
- API flows are understandable to architects and easy to inspect.
- Runtime traces are powerful but harder to collect consistently `[Dynamic2024]`
  `[StaticDynamic2020]`.
- Method-level dependencies can be expensive and noisy.
- Embeddings are useful, but should not become an unexplainable shortcut.

### V2 Acceptance Criteria

V2 is useful only if every new evidence signal has an ablation.

Call V2 done when:

1. At least two new evidence types are implemented.
2. Each has stable IDs and schema validation.
3. Generator and Refiner can cite the new IDs.
4. Quality Gate validates the new citations.
5. Ablation rows show whether each evidence type helped.
6. The paper can say which evidence signals matter and which do not.

## V3 - Smarter Agentic Search And Governance

V3 should improve the reasoning loop itself. This is where the framework becomes
more genuinely agentic.

Do not start V3 until V1 reliability and V2 evidence ablations are clear.
Otherwise, smarter orchestration will hide basic artifact problems.

### V3 Candidate Search Ideas

| Idea | Description | Risk |
|------|-------------|------|
| Candidate committee | Several generator agents with different assumptions. | More cost and harder attribution. |
| Critic agent | Reviews candidates before metric scoring. | Can become vague unless schema-bound. |
| Debate between strategies | Dependency-first and domain-first critique each other. | Expensive and prompt-sensitive. |
| Search tree refinement | Explore several patch paths instead of one. | Needs pruning and budget control. |
| Pareto selection `[MOO2022]` `[MOO2024]` | Keep candidates that trade off metrics differently. | More complex final selection. |
| Self-consistency voting | Generate many decompositions and cluster assignments. | May amplify common LLM bias. |
| Local deterministic repair | Fix obvious violations before LLM refinement. | Could mask generator weaknesses. |

### V3 Quality Governance Ideas

The MVP Quality Gate checks structural validity and grounding. V3 can turn it
into a broader governance layer. Data, quality-attribute, and granularity
concerns are literature-facing motivations for this expansion
`[DataCentric2022]` `[QualityAttributes2022]` `[Granularity2020]`.

Add rules for:

- data ownership conflicts;
- cross-service transaction risk;
- too many synchronous dependencies;
- service size imbalance;
- god service detection;
- anemic service detection;
- endpoint split across multiple services;
- circular dependency severity, not just count;
- missing business capability coverage;
- overfitting to package names;
- unsupported domain claims;
- hallucinated technologies or APIs.

For each rule, record:

| Field | Purpose |
|-------|---------|
| rule_id | Stable name for analysis. |
| severity | `info`, `warning`, or `error`. |
| evidence_refs | What evidence triggered it. |
| affected_services | Services involved. |
| suggested_action | What Refiner should consider. |
| ablation_flag | Whether the rule can be disabled for study. |

### V3 Refiner Improvements

The MVP Refiner applies one controlled patch. V3 can make refinement more
powerful while staying bounded.

Possible improvements:

1. Multi-round refinement with a maximum budget.
2. Several competing patches per round.
3. Deterministic pre-repair before LLM patching.
4. Metric-targeted refinement, such as cycle repair or service balance repair
  `[MOO2022]` `[MOO2024]`.
5. Patch confidence estimates.
6. Rollback when a patch harms reference or structural metrics.
7. Patch explanation report for each changed class.

Important rule:

```text
The Refiner should propose operations. The deterministic patcher should apply
operations. The Evaluator should decide whether the result is better.
```

Do not let the Refiner directly rewrite final JSON without operation checks.

### V3 Acceptance Criteria

Call V3 successful when:

1. Search produces multiple meaningfully different candidates.
2. Governance rules explain why candidates fail.
3. Refiner patches improve targeted violations more often than they introduce
   new ones.
4. Cost and latency remain reportable.
5. The paper can separate the effect of evidence, generation, governance, and
   refinement.

## V4 - Human-In-The-Loop Workbench

V4 is optional for the main research paper, but valuable for demos and follow-up
work.

The idea is to help a human architect inspect the decomposition process rather
than only read JSON files.

Possible workbench features:

| Feature | Value |
|---------|-------|
| Artifact timeline | Shows each agent output in order. |
| Service graph view | Shows service dependencies and cycles. |
| Class assignment table | Lets user inspect where every class went. |
| Evidence citation viewer | Shows why a class/service was assigned. |
| Metric dashboard | Compares B0/A1/A2/A3 and ablations. |
| Patch diff viewer | Shows what refinement changed. |
| Quality violation panel | Groups violations by severity and service. |
| Manual override experiment | Lets architect move classes and rescore. |
| Export report | Produces paper appendix or case-study report. |

Research question for V4:

```text
Does the framework help architects reason about decomposition, even when its
final boundary does not exactly match the reference decomposition?
```

This matters because the old paper found that LLMs may be structurally clean but
not reference-accurate. A workbench may still be valuable if it exposes tradeoffs
and evidence clearly.

## V5 - Publication And Replication Package

V5 is the paper-facing version. It should make the study reproducible by someone
outside this machine.

### V5 Must Include

| Item | Purpose |
|------|---------|
| Exact setup instructions | Reproducibility. |
| Benchmark system list | Scope of evaluation. |
| Prompt files | Allows review of LLM instructions. |
| Artifact schemas | Defines contracts. |
| Run configs | Defines experiment variants. |
| Raw run artifacts | Supports audit and replication. |
| Aggregated CSVs | Supports tables and plots. |
| Failure log | Avoids hiding bad runs. |
| Cost/token report | Makes agentic overhead explicit. |
| Result interpretation guide | Connects numbers to research claims. |

### V5 Paper Structure

A likely paper structure:

1. Introduction
2. Background: microservice decomposition and Wang benchmark
3. Problem: single-shot LLM decomposition limits
4. Framework: evidence, domain, generation, evaluation, governance, refinement
5. Implementation: artifact contracts, agents, metrics, run pipeline
6. Research questions
7. Experimental setup
8. Results
9. Ablation study
10. Failure analysis
11. Threats to validity
12. Discussion and future work
13. Conclusion

### Suggested Research Questions

Use these or adapt them:

| RQ | Question |
|----|----------|
| RQ1 | Can the multi-agent framework produce schema-valid, structurally sound decompositions across benchmark monoliths? |
| RQ2 | Does evaluator-guided candidate selection improve structural metrics compared with single-shot generation? |
| RQ3 | Does refinement reduce quality violations or improve metric outcomes? |
| RQ4 | Which agentic components contribute most to decomposition quality? |
| RQ5 | Does richer evidence improve recovery of reference service boundaries? |
| RQ6 | What are the main failure modes of LLM-based architecture decomposition? |
| RQ7 | What is the cost and latency overhead of agentic decomposition compared with B0? |

### Threats To Validity To Track Early

Do not leave these until the paper draft.

| Threat | How To Mitigate |
|--------|-----------------|
| Small benchmark set | Be explicit: four systems are inherited from the old setup. |
| Reference decomposition ambiguity | Report both reference metrics and structural metrics. |
| LLM nondeterminism | Use repeated runs and variance reporting. |
| Prompt overfitting | Keep prompts stable, log versions, use ablations. |
| Metric engine dependency | Record engine path/version and null metric causes. |
| Cost constraints | Report token/cost tradeoffs. |
| Evidence extraction errors | Validate evidence and include failure examples. |
| Human interpretation bias | Use predefined analysis questions and tables. |
| API/provider drift | Record model identifiers and run dates. |
| Dataset contamination | Avoid claims that require proving model training history. |

## Should Versus Could

When deciding what to build next, use this split.

### Should Build Before Major Claims

- reliable all-system real runs;
- repeated-run aggregation;
- cost/token summaries;
- failure classification;
- artifact audit command;
- stronger run-result tables;
- at least one richer evidence signal with ablation, preferably data ownership
  first `[DataCentric2022]`;
- paper-ready threat tracking;
- tests for deterministic quality/refinement logic.

### Could Build If Time Allows

- interactive workbench;
- runtime trace extraction;
- method-level dependency graph;
- candidate debate;
- Pareto frontier search `[MOO2022]` `[MOO2024]`;
- human architect scoring study;
- HTML reports;
- parallel experiment runner;
- prompt cache;
- CI pipeline.

### Should Not Build Yet

Avoid these until V1 results are clear:

- fully autonomous multi-agent conversation frameworks;
- free-form agents that can modify artifacts without schemas;
- new metrics that replace Wang metrics;
- large UI before core result stability;
- many new prompts without ablation switches;
- complex optimization algorithms without a failure analysis.

## Detailed Step Plan After Initial Linux Testing

Follow this order exactly unless the first test reveals a blocker.

### Step 1 - Run One Real MVP Trial

Command:

```bash
python -m agentic_decomposer run --config configs/mvp_jpetstore.yaml --run-id mvp_jpetstore_real_001
```

Record:

- model name;
- provider;
- run date;
- total runtime;
- token use;
- cost if available;
- metric engine status;
- whether each artifact exists;
- whether Quality Gate passed;
- whether refinement improved the selected candidate.

Stop if:

- the command crashes;
- metrics are null without clear reason;
- final output is missing;
- `decomposition.json` is missing;
- LLM logs are empty for a real run.

### Step 2 - Perform Manual Artifact Audit

Open the run folder and inspect the artifacts in order.

Write a short audit note with:

```text
Run ID:
System:
Model:
Status:
Best candidate:
Refinement accepted:
Quality violations:
Null metrics:
Obvious hallucinations:
Most suspicious service:
Most convincing service:
Next fix:
```

This note is more useful than a raw metric table at the beginning.

### Step 3 - Run One Ablation Batch

Command:

```bash
python agentic_decomposer/experiments/run_ablation.py --system jpetstore-6 --runs 1
```

Expected variants:

- `B0_single_shot`
- `A1_gen_only`
- `A2_eval_select`
- `A3_refined`
- `A_no_domain`
- `A_no_qg`
- `A_1cand_refined`

Ask:

- Does B0 scoring work?
- Does A3 improve over A1 or A2?
- Does removing the Domain Agent hurt anything?
- Does removing Quality Gate allow bad candidates through?
- Does one candidate plus refinement perform worse than multi-candidate search?

### Step 4 - Repeat Runs

After one ablation batch works, repeat each key variant at least three times.

Reason:

```text
One run shows feasibility. Repeated runs show whether the result is stable.
```

Track mean, median, standard deviation, best, worst, and failure count.

### Step 5 - Scale To All Four Systems

Run all systems only after JPetStore is understood.

Command family:

```bash
python -m agentic_decomposer run --config configs/mvp_all_systems.yaml --system all
python agentic_decomposer/experiments/run_ablation.py --system all --runs 3
```

For each system, write a short case note:

| Field | Description |
|-------|-------------|
| system | Benchmark name. |
| easiest evidence | Which evidence was most useful. |
| hardest ambiguity | What confused the model. |
| best variant | Which variant looked strongest. |
| worst failure | Most important failure mode. |
| metric surprise | Metric result that needs explanation. |

### Step 6 - Freeze V1 Baseline

When all-system repeated runs work, freeze a baseline:

- keep prompts unchanged;
- keep configs unchanged;
- keep schema versions unchanged;
- record exact model names;
- export aggregated CSVs;
- save failure logs;
- write a short V1 result summary.

Do not tune prompts while collecting baseline runs. If prompts change, start a
new version label.

### Step 7 - Choose One V2 Evidence Signal

Pick exactly one first. Recommended first choice after the literature scan:
database/entity ownership evidence `[DataCentric2022]`.

Fallback choice if data extraction is blocked: repository co-change or
repository-mining evidence `[OfflineMining2022]`.

Reason:

- data ownership is a central microservice-boundary concern in the scanned
  literature `[DataCentric2022]`;
- it tests a new source of architectural signal;
- it is explainable;
- it may improve cohesion and boundary recovery;
- it can be ablated cleanly.

Define before coding:

```text
Evidence source:
Raw extraction method:
Normalized artifact shape:
ID prefix:
Prompt exposure format:
Quality Gate rule:
Expected metric improvement:
Ablation variant:
Failure modes:
```

### Step 8 - Add The Evidence Signal

Implementation order:

1. Add extractor module.
2. Extend schema or add new schema.
3. Mint stable IDs.
4. Update Evidence Constructor.
5. Update prompt context.
6. Update Quality Gate citation checks.
7. Update docs.
8. Add ablation flag.
9. Run deterministic/no-API checks.
10. Run one real comparison.

### Step 9 - Compare V1 And V2

Do not ask whether V2 feels better. Ask whether it changes the result table.

Compare:

- structural metrics;
- reference-boundary metrics;
- violation counts;
- evidence coverage;
- candidate diversity;
- cost;
- failure modes.

If V2 improves only rationale text but not assignments, say that clearly.
That is still a useful research result.

### Step 10 - Decide V3 Scope

Only choose V3 after V2 tells you where the bottleneck is.

| If Bottleneck Is... | Build... |
|---------------------|----------|
| Bad evidence | more evidence extractors, not smarter agents. |
| Bad candidate diversity | candidate committee or strategy redesign. |
| Bad structural validity | stronger Quality Governance and deterministic repair. |
| Bad refinement | targeted patch search and rollback. |
| Bad reference recovery | data/domain/history evidence and human analysis `[DataCentric2022]` `[OfflineMining2022]`. |
| High cost | caching, smaller models, fewer candidates, cheaper critic. |
| Poor interpretability | HTML report or workbench. |

## How To Avoid Research Drift

Every new feature must have a table entry like this before implementation:

```text
Feature:
Version:
Problem it addresses:
Artifact changed:
Agent changed:
Schema changed:
Prompt changed:
Metric expected to improve:
Ablation/control:
Failure mode it may introduce:
How we will know it worked:
```

If you cannot fill this out, the feature is not ready.

## Paper Claim Ladder

As versions mature, claims should grow carefully.

| Evidence Available | Claim You Can Make |
|--------------------|--------------------|
| MVP runs once | Feasibility only. |
| V1 repeated runs | Agentic framework can be evaluated systematically. |
| V1 ablations | Some components contribute measurable effects. |
| V2 evidence ablations | Certain evidence sources help or do not help decomposition. |
| V3 governance/refinement results | Iterative quality-aware search changes decomposition outcomes. |
| Human/workbench study | Framework supports architect understanding and steering. |

Do not claim that the framework finds correct microservices unless reference
metrics support it. The safer and more interesting claim may remain:

```text
Agentic decomposition improves grounding, inspectability, and structural control,
while reference-boundary recovery remains a hard architecture problem.
```

## Final Post-MVP Checklist

Before declaring the next version complete, check:

- every new artifact has a schema;
- every new prompt has an output contract;
- every new LLM behavior has logs;
- every new metric or quality rule has docs;
- every new feature has an ablation or control;
- every result table can be regenerated;
- every failure type is counted;
- every paper claim is backed by a specific table or artifact;
- no API secrets are stored in repo files;
- generated run outputs are ignored unless intentionally archived.

## Where To Continue Reading

- Start with the current implemented architecture in [04-controller-and-run-lifecycle.md](04-controller-and-run-lifecycle.md).
- Review experiment interpretation in [07-experiments-and-results.md](07-experiments-and-results.md).
- Use [08-extension-playbook.md](08-extension-playbook.md) before changing schemas or agents.
- Use [10-llm-prompts-logging.md](10-llm-prompts-logging.md) before changing prompts or LLM behavior.
- Use [11-source-file-index.md](11-source-file-index.md) to find the exact files to edit.

The goal after MVP is not to make the system bigger as fast as possible. The
goal is to make each added capability test a clear research hypothesis.
