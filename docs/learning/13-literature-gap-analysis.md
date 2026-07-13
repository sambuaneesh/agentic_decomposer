# 13 - Literature Gap Analysis And Research Plan

This document records a focused web-based literature scan performed after the
MVP implementation and post-MVP roadmap were drafted.

It answers:

```text
Is the current framework enough, compared with the research field?
If not, what should we add, and in what order?
```

Short answer:

```text
The current MVP is enough for initial Linux testing and for a feasibility-stage
agentic decomposition study.

It is not enough, by itself, for the strongest possible paper claim. Before
making broad claims, we should add literature-facing baselines, stronger evidence
signals, repeated-run analysis, and a clearer comparison against existing
microservice-identification families.
```

## Scope Of The Scan

This was not a full systematic literature review. It was a focused roadmap scan
using public scholarly metadata and article pages where accessible.

Sources attempted:

- Crossref publication search and DOI metadata;
- DOI redirects to publisher pages;
- Semantic Scholar search;
- OpenAlex DOI lookup;
- arXiv API topic searches.

Access notes:

- Semantic Scholar returned rate-limit errors during this scan.
- Several publisher pages, including IEEE, ACM, Springer, and Elsevier pages,
  blocked automated content fetching with `403` responses.
- Crossref returned useful title, year, author, venue, and DOI metadata.
- arXiv queries did not return useful matches for the exact topic strings used.

Therefore, treat this document as a planning map, not a final related-work
section. Before paper submission, manually read the most important full papers.

## Citation Style And Evidence Rules

This document uses bracketed citation keys such as `[ServiceCutter2016]` and
`[Mono2Micro2021]`. The full references and DOI links are listed in
[References](#references).

Interpret the citations carefully:

- A citation next to a literature family means that the family or research
   direction is grounded in that paper's title/metadata and, where available,
   public bibliographic context.
- A citation next to a roadmap recommendation means the recommendation was
   inferred from that research direction, not that the cited paper explicitly
   recommends our exact implementation.
- Recommendations without a citation are engineering/reproducibility needs from
   this framework's own design, such as schema validation, run audits, and link
   checks.
- Because several full-text publisher pages were blocked, this document avoids
   detailed claims about paper internals unless those claims are obvious from the
   title, venue, and established framing of the work. Full manual reading is
   required before using these references in a submitted paper.

## Representative Papers Found

The following papers are important because they define the neighboring research
families our framework must position itself against.

| Key | Area | Representative Paper | Why It Matters |
|-----|------|----------------------|----------------|
| `[ServiceCutter2016]` | Systematic service decomposition | Gysel et al., `Service Cutter: A Systematic Approach to Service Decomposition`, 2016. | Classic criteria-driven service decomposition reference point. |
| `[Mono2Micro2021]` | Industrial AI decomposition tool | Kalia et al., `Mono2Micro: a practical and effective tool for decomposing monolithic Java applications to microservices`, 2021. | Strong industrial baseline and toolchain comparison point. |
| `[MOO2022]` | Multi-objective optimization | Kinoshita and Kanuka, `Automated Microservice Decomposition Method as Multi-Objective Optimization`, 2022. | Frames decomposition as optimization over competing objectives. |
| `[MOO2024]` | Improved multi-objective optimization | Kinoshita and Kanuka, `Enhancing Automated Microservice Decomposition via Multi-Objective Optimization`, 2024. | Recent continuation of optimization-based decomposition. |
| `[KG2022]` | Knowledge graph extraction | Li et al., `Microservice extraction based on knowledge graph from monolithic applications`, 2022. | Supports explicit graph/evidence modeling as a future direction. |
| `[DataCentric2022]` | Data-centric identification | Romani et al., `Towards Migrating Legacy Software Systems to Microservice-based Architectures: a Data-Centric Process for Microservice Identification`, 2022. | Supports making data ownership a first-class evidence signal. |
| `[Granularity2020]` | Granularity mapping | Hassan, Bahsoon, and Kazman, `Microservice transition and its granularity problem: A systematic mapping study`, 2020. | Supports explicit service granularity diagnostics. |
| `[QualityAttributes2022]` | Quality attributes | Capuano and Muccini, `A Systematic Literature Review on Migration to Microservices: a Quality Attributes perspective`, 2022. | Supports evaluation beyond boundary similarity alone. |
| `[Review2024]` | Microservice identification review | Oumoussa and Saidi, `Evolution of Microservices Identification in Monolith Decomposition: A Systematic Review`, 2024. | Supports broad baseline/taxonomy positioning. |
| `[Ontology2025]` | Ontology mapping | Oumoussa and Saidi, `The Ontology-Based Mapping of Microservice Identification Approaches`, 2025. | Supports taxonomy/ontology-aware related-work mapping. |
| `[SemanticReview2025]` | Semantic approaches review | Ait Mansour et al., `Semantic Approaches to Microservice Identification: A Systematic Literature Review`, 2025. | Supports semantic/domain vocabulary evidence. |
| `[Dynamic2024]` | Dynamic decomposition | Ait Manssour et al., `Dynamic Decomposition of Monolith Applications Into Microservices Architectures`, 2024. | Supports runtime/dynamic evidence as a future direction. |
| `[StaticDynamic2020]` | Static/dynamic analysis | Krause, Zirkelbach, and Hasselbring, `Microservice Decomposition via Static and Dynamic Analysis of the Monolith`, 2020. | Supports combining static and dynamic signals. |
| `[OfflineMining2022]` | Repository/architecture mining | Soldani, Khalili, and Brogi, `Offline Mining of Microservice-based Architectures`, 2022. | Supports mining existing artifacts/repositories as evidence. |
| `[GRL2025]` | Graph reinforcement learning | Zhu, `Automated Microservice Decomposition Using Graph Reinforcement Learning for System Modernization`, 2025. | Shows newer ML/search framing outside LLMs. |
| `[Metaheuristic2025]` | Metaheuristic search | Martínez Saucedo et al., `A Novel Metaheuristic Approach to Monolith Decomposition into Microservices`, 2025. | Suggests search/optimization baselines for V3. |
| `[MLMigration2025]` | ML-driven migration meta-analysis | Mehmood et al., `Monolith to Microservices: A Systematic Meta-Analysis for Software Engineering Tasks and Machine Learning-Driven Migration`, 2025. | Helps place LLMs among broader ML-driven migration work. |
| `[MethodsReview2025]` | Decomposition-method review | Liu et al., `Review of Microservice Decomposition Methods`, 2025. | Another review signal for taxonomy and related-work completeness. |
| `[LLMArchKnowledge2025]` | LLM architectural knowledge | Soliman and Keim, `Do Large Language Models Contain Software Architectural Knowledge?: An Exploratory Case Study with GPT`, 2025. | Directly relevant to the LLM architecture-understanding claim. |
| `[LLMArchRecovery2026]` | LLM architecture recovery | De Luca et al., `Large Language Models for Software Architecture Recovery from Source Code: Class Diagrams, Patterns, Styles, and Architecture-as-Code Views`, 2026. | Relevant to LLM-based architecture extraction; status should be checked manually. |

## What The Field Seems To Care About

The scan suggests that microservice decomposition research is not one field. It
is several overlapping families, especially criteria-based decomposition,
industrial toolchains, optimization/search methods, knowledge-graph/semantic
methods, data-centric methods, runtime/dynamic methods, and LLM architecture
recovery `[ServiceCutter2016]` `[Mono2Micro2021]` `[MOO2022]` `[KG2022]`
`[DataCentric2022]` `[Dynamic2024]` `[LLMArchKnowledge2025]`.

### Family 1 - Rule And Criteria-Based Decomposition

Examples include Service Cutter-style approaches and later taxonomy/review work
that maps microservice-identification strategies `[ServiceCutter2016]`
`[Review2024]` `[Ontology2025]` `[MethodsReview2025]`.

Common signals:

- domain-driven design criteria;
- entity ownership;
- bounded contexts;
- use cases;
- coupling/cohesion rules;
- expert-provided context maps.

Implication for us:

```text
Our Domain Agent and Quality Gate should be framed as schema-bound,
LLM-assisted descendants of criteria-based decomposition, not as pure LLM magic.
```

What we already cover:

- domain capabilities;
- evidence citations;
- local quality rules;
- service responsibilities.

What is still weak:

- explicit DDD terminology;
- bounded-context modeling;
- aggregate/entity ownership;
- human-supplied domain constraints;
- comparison to criteria-driven tools.

### Family 2 - Industrial Toolchains

Mono2Micro is the most important industrial-tool representative in this scan;
ML-driven migration reviews also suggest that the framework should be positioned
against broader toolchain-style migration work `[Mono2Micro2021]`
`[MLMigration2025]`.

Common signals:

- static dependencies;
- runtime traces or use-case traces;
- business use cases;
- class clustering;
- tooling/reporting around migration;
- practical developer workflow.

Implication for us:

```text
If we compare only against the old single-shot LLM baseline, reviewers may ask
why we did not position against industrial decomposition tools.
```

What we already cover:

- static class dependencies;
- source-derived evidence;
- file-based run reports;
- benchmark-oriented metrics.

What is still weak:

- runtime traces;
- developer workflow;
- industrial-style migration recommendations;
- UI/reporting;
- practical migration steps after decomposition.

### Family 3 - Multi-Objective Optimization And Search

Recent papers treat decomposition as optimization or search over multiple
competing objectives `[MOO2022]` `[MOO2024]` `[Metaheuristic2025]` `[GRL2025]`.

Common objectives:

- minimize coupling;
- maximize cohesion;
- reduce cycles;
- balance service size;
- respect data ownership;
- preserve business capabilities;
- optimize granularity.

Implication for us:

```text
Our evaluator-selection-refiner loop is already close to search, but we should
make the connection explicit and eventually support Pareto-style comparison.
```

What we already cover:

- multiple candidates;
- composite score;
- external metrics;
- refinement and re-evaluation.

What is still weak:

- Pareto frontier reporting;
- explicit objective weights and sensitivity analysis;
- comparison to optimization baselines;
- search budget reporting;
- deterministic search alternatives.

### Family 4 - Knowledge Graph And Semantic Approaches

Knowledge graph and semantic literature is close to our evidence-artifact model
`[KG2022]` `[SemanticReview2025]` `[Ontology2025]`.

Common signals:

- class relations;
- method calls;
- package structure;
- entities and data flows;
- semantic similarity;
- business vocabulary;
- graph centrality/community structure.

Implication for us:

```text
Our evidence_pack can become a lightweight architecture knowledge graph, but the
MVP does not yet explicitly model it that way.
```

What we already cover:

- normalized evidence IDs;
- classes, APIs, persistence, technology, dependencies;
- evidence references in candidates.

What is still weak:

- explicit graph schema;
- graph queries;
- semantic relation types;
- graph-based clustering baseline;
- ontology/taxonomy alignment.

### Family 5 - Data-Centric Identification

Data ownership is a recurring theme in microservice migration and quality-aware
identification work `[DataCentric2022]` `[QualityAttributes2022]` `[KG2022]`.

Common signals:

- database tables;
- entity classes;
- repositories/DAOs;
- transactions;
- shared tables;
- CRUD ownership;
- read/write patterns.

Implication for us:

```text
A strong V2 should add data ownership evidence before adding exotic agents.
```

What we already cover:

- deterministic persistence artifacts in A4;
- DTP metric integration if the metric engine provides it.

What is still weak:

- table/entity-to-service ownership;
- repository-to-entity mapping;
- transaction boundary detection;
- shared-data violation checks;
- data ownership quality gate rules.

### Family 6 - Dynamic And Runtime Evidence

Some decomposition methods use runtime behavior, dynamic analysis, or scenario
signals `[Dynamic2024]` `[StaticDynamic2020]` `[Mono2Micro2021]`.

Common signals:

- endpoint execution traces;
- class participation per use case;
- call sequences;
- transaction traces;
- observed runtime dependencies;
- scenario-based clustering.

Implication for us:

```text
Runtime evidence is not necessary for initial testing, but it is an important
future differentiator and comparison point.
```

What we already cover:

- endpoints statically;
- static dependency graph;
- optional future runtime traces in the roadmap.

What is still weak:

- instrumentation strategy;
- scenario selection;
- trace-to-class mapping;
- dynamic evidence schema;
- repeatable execution across benchmark apps.

### Family 7 - LLM Architecture Understanding And Recovery

Newer research asks whether LLMs contain architectural knowledge or can recover
architecture views from source code `[LLMArchKnowledge2025]`
`[LLMArchRecovery2026]`.

Common tasks:

- architecture recovery;
- class diagrams;
- style/pattern detection;
- architecture-as-code views;
- design rationale generation;
- architecture decision support.

Implication for us:

```text
Our contribution should be framed as LLM-assisted architectural decomposition
with evidence, evaluation, and governance, not merely LLM architecture recovery.
```

What we already cover:

- LLM evidence extraction;
- LLM domain extraction;
- LLM candidate generation;
- LLM refinement;
- local schema and quality checks.

What is still weak:

- explicit comparison to LLM architecture-recovery tasks;
- benchmarked prompt variants;
- model comparison;
- hallucination analysis;
- architectural-view accuracy beyond service boundaries.

## Is The Current Framework Enough?

### Enough For MVP And Initial Testing

Yes. The current framework is enough to test:

- whether a multi-agent pipeline can run end-to-end;
- whether artifacts are valid and inspectable;
- whether LLM output can be grounded in evidence IDs;
- whether evaluator/refiner loops improve local structural quality;
- whether old B0-style output can be compared against the new framework.

For this stage, do not add more features before running Linux tests.

### Not Enough For A Strong Final Paper By Itself

If the final paper only says:

```text
We built a multi-agent LLM framework and compared it to our old single-shot LLM
baseline.
```

reviewers may ask questions grounded in these neighboring families
`[ServiceCutter2016]` `[Mono2Micro2021]` `[MOO2022]` `[MOO2024]`
`[DataCentric2022]` `[Dynamic2024]` `[Granularity2020]`
`[LLMArchKnowledge2025]`:

- Where are non-LLM decomposition baselines?
- How does this relate to Service Cutter and Mono2Micro?
- How does it compare to optimization-based decomposition?
- Does it use data ownership evidence?
- Does it use dynamic/runtime evidence?
- Does it handle granularity explicitly?
- Are results stable across LLM runs?
- Is the improvement worth the cost?
- Does richer evidence improve reference-boundary recovery?

So the answer is:

```text
Current implementation: enough for feasibility and V1 baseline.
Research program: needs more comparison, evidence, and analysis before strong
claims.
```

## Gaps We Should Address

### Gap 1 - Baseline Positioning

Literature basis: criteria-based decomposition, industrial decomposition tools,
optimization/search methods, and review papers `[ServiceCutter2016]`
`[Mono2Micro2021]` `[MOO2022]` `[MOO2024]` `[Review2024]`
`[MethodsReview2025]`.

Current state:

- We compare against old B0-style single-shot LLM output and Wang-style metrics.

Needed:

- Determine exactly which baselines the old accepted paper already includes.
- If existing decomposition tools are already represented in old results, document
  that clearly.
- If not, add at least conceptual or runnable comparison against representative
  non-LLM methods.

Recommended actions:

1. Open the old paper artifacts and list every baseline/tool already compared.
2. Create a `baselines.md` doc mapping:

```text
B0 old LLM baseline
Wang reference decomposition
existing decomposition tools from old paper
new agentic variants
future non-LLM baselines
```

3. Decide whether Service Cutter/Mono2Micro can be run or only discussed
   `[ServiceCutter2016]` `[Mono2Micro2021]`.
4. If they cannot be run, be explicit in threats to validity.

Priority: high.

### Gap 2 - Data Ownership Evidence

Literature basis: data-centric microservice identification and quality-attribute
evaluation `[DataCentric2022]` `[QualityAttributes2022]`; knowledge-graph
extraction also points toward explicit entity/data relations `[KG2022]`.

Current state:

- A4 persistence exists, but data ownership is not yet a first-class artifact.

Needed:

- entity/table/repository mapping;
- CRUD ownership classification;
- shared-data risk detection;
- service-to-data ownership report.

Recommended actions:

1. Add a data ownership extractor.
2. Add stable IDs such as `D_001` for data entities/tables.
3. Extend candidate rationale rules to cite data IDs.
4. Add Quality Gate rules for data ownership conflicts.
5. Add ablation variant `A_no_data_evidence`.
6. Compare DTP and service-boundary changes.

Priority: very high for V2.

### Gap 3 - Knowledge Graph Or Semantic Evidence Model

Literature basis: knowledge-graph extraction, semantic identification reviews,
and ontology-based mapping `[KG2022]` `[SemanticReview2025]` `[Ontology2025]`.

Current state:

- Evidence is structured JSON, but not explicitly treated as a graph.

Needed:

- graph-shaped relation model;
- relation types such as `calls`, `owns_data`, `handles_endpoint`,
  `implements_capability`, `co_changes_with`;
- graph export for inspection;
- graph-based clustering baseline or diagnostic.

Recommended actions:

1. Add `architecture_graph.json` as a derived artifact or export.
2. Keep `evidence_pack.json`; do not replace it immediately.
3. Add deterministic graph queries for prompt compaction.
4. Add community-detection baseline for comparison.
5. Add graph coverage diagnostics.

Priority: high for V2/V3.

### Gap 4 - Runtime/Dynamic Evidence

Literature basis: dynamic decomposition, static/dynamic monolith analysis, and
industrial toolchain work `[Dynamic2024]` `[StaticDynamic2020]`
`[Mono2Micro2021]`.

Current state:

- Static endpoints and dependencies exist; runtime traces are not implemented.

Needed:

- scenario execution plan;
- trace collection strategy;
- endpoint-to-class participation mapping;
- trace evidence IDs;
- trace-aware generator/refiner context.

Recommended actions:

1. Start with JPetStore because it is likely easiest to run and inspect.
2. Define 3 to 5 scenarios per benchmark system.
3. Capture traces with a lightweight Java agent, logs, or framework hooks.
4. Store `TR_...` evidence IDs.
5. Add `A_no_trace_evidence` ablation.

Priority: medium-high, but only after V1 and data evidence.

### Gap 5 - Granularity Control

Literature basis: granularity is explicitly identified as a microservice
transition problem in systematic mapping work `[Granularity2020]`.

Current state:

- Service count constraints exist, and `num_services` is recorded.

Needed:

- explicit granularity objective;
- service-size balance diagnostics;
- over-splitting and under-splitting checks;
- comparison across target service counts;
- sensitivity analysis.

Recommended actions:

1. Add diagnostics for largest service ratio, smallest service size, and service
   count distance from reference.
2. Run variants with different `min_services`/`max_services` ranges.
3. Add a granularity section to the final output.
4. Report whether the framework improves structure by simply changing service
   count.

Priority: high for paper credibility.

### Gap 6 - Multi-Objective And Pareto Comparison

Literature basis: multi-objective optimization, metaheuristic search, and graph
reinforcement-learning approaches `[MOO2022]` `[MOO2024]`
`[Metaheuristic2025]` `[GRL2025]`.

Current state:

- Composite score chooses a single best candidate.

Needed:

- preserve candidates with different tradeoffs;
- show Pareto frontier over metrics;
- report when no candidate dominates;
- avoid hiding tradeoffs behind one weighted score.

Recommended actions:

1. Keep composite score for controller selection.
2. Add Pareto-frontier reporting for analysis.
3. Add sensitivity analysis over composite weights.
4. Compare A2/A3 against a simple deterministic search baseline if feasible.

Priority: medium-high for V3.

### Gap 7 - LLM Variance And Cost

Literature basis: the scan found LLM architecture-understanding and
architecture-recovery papers, which motivates treating LLM behavior as an
experimental variable `[LLMArchKnowledge2025]` `[LLMArchRecovery2026]`.
The exact repeat/cost protocol is our framework's reproducibility requirement,
not a direct prescription from those papers.

Current state:

- Token logging exists, repeated-run planning exists, but analysis tooling still
  needs to be built.

Needed:

- repeated-run aggregation;
- variance reporting;
- failure rates;
- token/cost per artifact and per agent;
- model comparison.

Recommended actions:

1. Run at least 3 repeats per key variant, ideally 5 if cost allows.
2. Aggregate mean, median, standard deviation, best, worst.
3. Report token/cost per variant.
4. Try one cheaper model as a cost-control ablation.

Priority: very high for any LLM paper.

### Gap 8 - Human/Architect Evaluation

Literature basis: quality-attribute migration work and industrial/toolchain
positioning suggest that metric-only evaluation may be too narrow
`[QualityAttributes2022]` `[Mono2Micro2021]`. The proposed human audit is a
framework recommendation that should be justified manually if promoted to a
formal study.

Current state:

- Metrics and Quality Gate are machine-driven.

Needed:

- qualitative inspection;
- expert or developer judgment;
- rationale usefulness scoring;
- failure examples.

Recommended actions:

1. Start with internal manual audit notes, not a formal user study.
2. Create a rubric for service-name clarity, responsibility coherence, evidence
   usefulness, and suspicious boundaries.
3. If time allows, ask 2 to 3 developers/architects to rank anonymized variants.
4. Use human evaluation as supplementary evidence, not the main claim.

Priority: medium for MVP paper, high for extended paper.

### Gap 9 - Migration Practicality

Literature basis: industrial decomposition and ML-driven migration framing
suggest that practical migration support is a neighboring concern
`[Mono2Micro2021]` `[MLMigration2025]` `[QualityAttributes2022]`.

Current state:

- The framework produces decomposition suggestions, not migration plans.

Needed:

- migration risk notes;
- dependency-breaking steps;
- data split warnings;
- strangler-fig extraction order;
- API ownership map.

Recommended actions:

1. Keep this out of MVP unless paper scope expands.
2. Add it as future work or V4/V5 extension.
3. If implemented, make it another artifact, not prose hidden in final output.

Priority: low for current research claim, high for industry demo.

## Updated Recommendation

The previous post-MVP roadmap is directionally correct. This literature scan
changes the emphasis.

### Before Initial Testing

Do nothing more except run and inspect.

Reason:

```text
The current MVP must be tested before we add literature-driven complexity.
```

### Immediately After Initial Testing

V1 should focus on reliability and result credibility. This is primarily a
framework reproducibility need, but it is also required before comparing against
the broad method families in the review and baseline literature `[Review2024]`
`[MethodsReview2025]`:

1. repeated runs;
2. aggregation;
3. failure classification;
4. cost/token reporting;
5. baseline documentation;
6. artifact audit command;
7. granularity diagnostics.

### First Research Expansion

V2 should prioritize evidence types that the literature makes hard to ignore:

1. data ownership evidence `[DataCentric2022]` `[QualityAttributes2022]`;
2. knowledge-graph/semantic evidence representation `[KG2022]`
   `[SemanticReview2025]` `[Ontology2025]`;
3. repository/mining or co-change evidence `[OfflineMining2022]`;
4. trace evidence only after the first two are stable `[Dynamic2024]`
   `[StaticDynamic2020]`.

### Second Research Expansion

V3 should prioritize search and objective analysis because decomposition is
often framed as multi-objective or search-based optimization `[MOO2022]`
`[MOO2024]` `[Metaheuristic2025]` `[GRL2025]`:

1. Pareto-frontier reporting;
2. multi-objective objective analysis;
3. stronger Quality Governance;
4. targeted refiner patch search;
5. comparison to search/optimization families.

### Optional Later Expansion

V4/V5 can add:

- workbench UI;
- human architect evaluation;
- migration-plan artifacts;
- replication package.

## Revised Version Plan

### MVP - Keep As Is

Do not add literature features before the first real run.

MVP claim:

```text
A schema-bound multi-agent LLM decomposition pipeline can produce inspectable
artifacts and be evaluated against existing metrics.
```

### V1 - Credibility Layer

Add:

- result aggregation;
- cost/variance analysis;
- failure taxonomy;
- baseline inventory;
- granularity diagnostics;
- artifact audit command.

V1 claim:

```text
The framework can be evaluated systematically across systems, variants, and
repeated LLM runs.
```

### V2 - Evidence Layer

Add:

- data ownership evidence `[DataCentric2022]`;
- architecture knowledge graph export `[KG2022]`;
- semantic/domain vocabulary evidence `[SemanticReview2025]` `[Ontology2025]`;
- co-change or repository-mining evidence `[OfflineMining2022]`;
- ablations for each evidence source.

V2 claim:

```text
Richer architecture evidence can be measured for its effect on decomposition
quality, rather than assumed to help.
```

### V3 - Search And Governance Layer

Add:

- Pareto frontier `[MOO2022]` `[MOO2024]`;
- objective sensitivity `[MOO2022]` `[MOO2024]`;
- stronger Quality Governance;
- targeted refiner search;
- optimization-family comparison `[Metaheuristic2025]` `[GRL2025]`.

V3 claim:

```text
Agentic decomposition can be treated as quality-governed search over competing
architectural objectives.
```

### V4 - Human And Migration Layer

Add:

- architect review workflow;
- visual artifact report;
- manual override and rescore;
- migration-risk notes `[QualityAttributes2022]` `[MLMigration2025]`;
- extraction-order hints.

V4 claim:

```text
Even when exact reference-boundary recovery is hard, the framework can support
architectural reasoning and migration planning.
```

## What We Need To Work On More

Prioritized list:

| Priority | Work | Why |
|----------|------|-----|
| 1 | Run MVP on Linux and inspect artifacts. | Without real outputs, all planning is speculative. |
| 2 | Build result aggregation and repeated-run analysis. | Needed before comparing against reviewed method families and LLM architecture work `[Review2024]` `[LLMArchKnowledge2025]`. |
| 3 | Create baseline inventory against old paper and known tools. | Prevent weak positioning against criteria/tool/optimization baselines `[ServiceCutter2016]` `[Mono2Micro2021]` `[MOO2022]`. |
| 4 | Add granularity diagnostics. | Granularity is central in decomposition literature `[Granularity2020]`. |
| 5 | Add data ownership evidence. | Data-centric identification is too important to omit long-term `[DataCentric2022]`. |
| 6 | Add knowledge graph or semantic evidence layer. | Aligns with semantic/knowledge-graph approaches `[KG2022]` `[SemanticReview2025]`. |
| 7 | Add co-change or repository-mining evidence. | Adds repository/evolutionary signal missing from source-only decomposition `[OfflineMining2022]`. |
| 8 | Add Pareto/multi-objective analysis. | Aligns with optimization literature and avoids hiding tradeoffs `[MOO2022]` `[MOO2024]`. |
| 9 | Add runtime traces if feasible. | Important but heavier operationally `[Dynamic2024]` `[StaticDynamic2020]`. |
| 10 | Add human/architect audit. | Strengthens quality-attribute and tool-use interpretation `[QualityAttributes2022]` `[Mono2Micro2021]`. |

## What Not To Overbuild Yet

Do not rush into:

- autonomous agent frameworks without stronger evidence;
- UI before result stability;
- runtime tracing before data ownership;
- new metrics that replace Wang metrics;
- model-vs-model leaderboard before artifact quality is stable;
- migration-plan generation before decomposition reliability is understood.

These may be good later, but they are not the next bottleneck.

## Suggested Paper Positioning

The strongest positioning is probably not:

```text
LLMs solve microservice decomposition.
```

A stronger and safer positioning is:

```text
Single-shot LLM decomposition is hard to trust because it mixes evidence
recovery, domain reasoning, boundary generation, and evaluation in one opaque
step. We propose a schema-bound multi-agent framework that separates these
concerns, makes intermediate artifacts inspectable, and evaluates whether
agentic evidence, selection, and refinement improve structural quality and
boundary recovery.
```

This positioning connects to:

- LLM architecture understanding `[LLMArchKnowledge2025]`;
- architecture recovery `[LLMArchRecovery2026]`;
- microservice identification `[Review2024]` `[MethodsReview2025]`;
- semantic/knowledge-graph approaches `[KG2022]` `[SemanticReview2025]`;
- multi-objective decomposition `[MOO2022]` `[MOO2024]`;
- data-centric migration `[DataCentric2022]`;
- quality-governed architecture decision support `[QualityAttributes2022]`.

## Literature-To-Feature Matrix

| Literature Theme | Framework Feature Already Present | Needed Next |
|------------------|-----------------------------------|-------------|
| Service Cutter / criteria-based decomposition `[ServiceCutter2016]` | Domain Agent, Quality Gate. | DDD/bounded-context constraints and baseline discussion. |
| Mono2Micro / industrial toolchain `[Mono2Micro2021]` | static dependencies, artifacts, reports. | runtime traces, workflow reports, practical migration notes. |
| Multi-objective optimization `[MOO2022]` `[MOO2024]` | composite score, multiple candidates. | Pareto frontier and sensitivity analysis. |
| Knowledge graph extraction `[KG2022]` | evidence IDs and dependency graph. | explicit architecture graph artifact. |
| Data-centric decomposition `[DataCentric2022]` | persistence evidence, DTP metric. | data ownership extractor and data Quality Gate. |
| Semantic approaches `[SemanticReview2025]` `[Ontology2025]` | LLM domain extraction, class-capability matrix. | vocabulary/embedding/semantic evidence ablation. |
| Dynamic decomposition `[Dynamic2024]` `[StaticDynamic2020]` | endpoint evidence. | runtime traces/scenario evidence. |
| Granularity studies `[Granularity2020]` | min/max service constraints. | granularity diagnostics and service-count sensitivity. |
| LLM architecture recovery `[LLMArchKnowledge2025]` `[LLMArchRecovery2026]` | LLM evidence/domain/generator/refiner. | architecture-view accuracy and hallucination taxonomy. |
| ML/metaheuristic/GRL methods `[MLMigration2025]` `[Metaheuristic2025]` `[GRL2025]` | agentic search loop. | compare as search method, not just LLM method. |

## Concrete Next Docs To Add Later

After the first Linux run, add these docs if the project continues toward paper:

1. `docs/baseline_inventory.md`
   - old-paper baselines;
   - tool baselines;
   - reference decompositions;
   - what is runnable versus only discussed.

2. `docs/result_analysis_protocol.md`
   - repeated-run protocol;
   - metrics table schema;
   - failure taxonomy;
   - cost reporting.

3. `docs/data_ownership_evidence.md`
   - entity/table/repository extraction;
   - data IDs;
   - Quality Gate rules;
   - expected DTP effects.

4. `docs/architecture_graph.md`
   - graph schema;
   - relation types;
   - export format;
   - graph diagnostics.

5. `docs/related_work_map.md`
   - taxonomy of decomposition approaches;
   - where the agentic framework fits;
   - exact citations and manual paper notes.

## Final Judgment

The current work is complete for:

- implementation handoff;
- initial Linux testing;
- feasibility validation;
- first agentic-vs-single-shot comparison.

It is not complete for:

- a final high-confidence research paper `[Review2024]` `[MethodsReview2025]`;
- broad claims against all decomposition methods `[ServiceCutter2016]`
   `[Mono2Micro2021]` `[MOO2022]` `[MOO2024]`;
- strong claims about data ownership `[DataCentric2022]`;
- strong claims about runtime behavior `[Dynamic2024]` `[StaticDynamic2020]`;
- strong claims about optimal service granularity `[Granularity2020]`;
- strong claims about outperforming optimization or industrial tools
   `[Mono2Micro2021]` `[MOO2022]` `[MOO2024]` `[Metaheuristic2025]`.

The correct next move is not to rewrite the framework. The correct next move is:

```text
Run MVP -> inspect artifacts -> stabilize V1 -> add result aggregation and
baseline inventory -> then add data/semantic/graph evidence as V2.
```

That gives us a research path that is both ambitious and defensible.

## References

Metadata was gathered from Crossref search/DOI records where possible. Several
publisher pages blocked automated full-text fetching, so use these as planning
references and manually verify full paper details before submission.

`[ServiceCutter2016]` Michael Gysel, Lukas Kölbener, Wolfgang Giersche, Olaf
Zimmermann. `Service Cutter: A Systematic Approach to Service Decomposition`.
Lecture Notes in Computer Science, 2016. DOI:
[10.1007/978-3-319-44482-6_12](https://doi.org/10.1007/978-3-319-44482-6_12).

`[Mono2Micro2021]` Anup K. Kalia, Jin Xiao, Rahul Krishna, Saurabh Sinha.
`Mono2Micro: a practical and effective tool for decomposing monolithic Java
applications to microservices`. ESEC/FSE, 2021. DOI:
[10.1145/3468264.3473915](https://doi.org/10.1145/3468264.3473915).

`[MOO2022]` Takahiro Kinoshita, Hideyuki Kanuka. `Automated Microservice
Decomposition Method as Multi-Objective Optimization`. IEEE ICSA-C, 2022. DOI:
[10.1109/ICSA-C54293.2022.00028](https://doi.org/10.1109/ICSA-C54293.2022.00028).

`[MOO2024]` Takahiro Kinoshita, Hideyuki Kanuka. `Enhancing Automated
Microservice Decomposition via Multi-Objective Optimization`. IEEE Access,
2024. DOI:
[10.1109/ACCESS.2024.3389700](https://doi.org/10.1109/ACCESS.2024.3389700).

`[KG2022]` Zhiding Li, Chenqi Shang, Jianjie Wu, Yuan Li. `Microservice
extraction based on knowledge graph from monolithic applications`. Information
and Software Technology, 2022. DOI:
[10.1016/j.infsof.2022.106992](https://doi.org/10.1016/j.infsof.2022.106992).

`[DataCentric2022]` Yamina Romani, Okba Tibermacine, Chouki Tibermacine.
`Towards Migrating Legacy Software Systems to Microservice-based Architectures:
a Data-Centric Process for Microservice Identification`. IEEE ICSA-C, 2022.
DOI: [10.1109/ICSA-C54293.2022.00010](https://doi.org/10.1109/ICSA-C54293.2022.00010).

`[Granularity2020]` Sara Hassan, Rami Bahsoon, Rick Kazman. `Microservice
transition and its granularity problem: A systematic mapping study`. Software:
Practice and Experience, 2020. DOI:
[10.1002/spe.2869](https://doi.org/10.1002/spe.2869).

`[QualityAttributes2022]` Roberta Capuano, Henry Muccini. `A Systematic
Literature Review on Migration to Microservices: a Quality Attributes
perspective`. IEEE ICSA-C, 2022. DOI:
[10.1109/ICSA-C54293.2022.00030](https://doi.org/10.1109/ICSA-C54293.2022.00030).

`[Review2024]` Idris Oumoussa, Rajaa Saidi. `Evolution of Microservices
Identification in Monolith Decomposition: A Systematic Review`. IEEE Access,
2024. DOI:
[10.1109/ACCESS.2024.3365079](https://doi.org/10.1109/ACCESS.2024.3365079).

`[Ontology2025]` Idris Oumoussa, Rajaa Saidi. `The Ontology-Based Mapping of
Microservice Identification Approaches: A Systematic Study of Migration
Strategies from Monolithic to Microservice Architectures`. Computers, 2025.
DOI: [10.3390/computers14040133](https://doi.org/10.3390/computers14040133).

`[SemanticReview2025]` Nassima Ait Mansour, Sbai Hanae, Karim Baïna, Iman El
Kodssi. `Semantic Approaches to Microservice Identification: A Systematic
Literature Review`. IEEE Access, 2025. DOI:
[10.1109/ACCESS.2025.3618990](https://doi.org/10.1109/ACCESS.2025.3618990).

`[Dynamic2024]` Ait Manssour Nassima, Sbai Hanae, Baïna Karim. `Dynamic
Decomposition of Monolith Applications Into Microservices Architectures`. MSCC,
2024. DOI:
[10.1109/MSCC62288.2024.10697026](https://doi.org/10.1109/MSCC62288.2024.10697026).

`[StaticDynamic2020]` Alexander Krause, Christian Zirkelbach, Wilhelm
Hasselbring. `Microservice Decomposition via Static and Dynamic Analysis of the
Monolith`. IEEE ICSA-C, 2020. DOI:
[10.1109/ICSA-C50368.2020.00011](https://doi.org/10.1109/ICSA-C50368.2020.00011).

`[OfflineMining2022]` Jacopo Soldani, Javad Khalili, Antonio Brogi. `Offline
Mining of Microservice-based Architectures`. 2022. DOI:
[10.5220/0011061000003200](https://doi.org/10.5220/0011061000003200).

`[GRL2025]` Yuanjing Zhu. `Automated Microservice Decomposition Using Graph
Reinforcement Learning for System Modernization`. ICCASIT, 2025. DOI:
[10.1109/ICCASIT66611.2025.11348732](https://doi.org/10.1109/ICCASIT66611.2025.11348732).

`[Metaheuristic2025]` Ana Martínez Saucedo, Guillermo Rodríguez, Virginia
Yannibelli. `A Novel Metaheuristic Approach to Monolith Decomposition into
Microservices`. GECCO Companion, 2025. DOI:
[10.1145/3712255.3734273](https://doi.org/10.1145/3712255.3734273).

`[MLMigration2025]` Nadeem Mehmood, Gian Luca Scoccia, Marco Autili. `Monolith
to Microservices: A Systematic Meta-Analysis for Software Engineering Tasks and
Machine Learning-Driven Migration`. SSRN, 2025. DOI:
[10.2139/ssrn.5202515](https://doi.org/10.2139/ssrn.5202515).

`[MethodsReview2025]` Haibo Liu, Yongbin Bai, Ziao Xu, Wenhua Yu. `Review of
Microservice Decomposition Methods`. ICCECT, 2025. DOI:
[10.1109/ICCECT64621.2025.11339597](https://doi.org/10.1109/ICCECT64621.2025.11339597).

`[LLMArchKnowledge2025]` Mohamed Soliman, Jan Keim. `Do Large Language Models
Contain Software Architectural Knowledge?: An Exploratory Case Study with GPT`.
IEEE ICSA, 2025. DOI:
[10.1109/ICSA65012.2025.00012](https://doi.org/10.1109/ICSA65012.2025.00012).

`[LLMArchRecovery2026]` Marco De Luca, Domenico Amalfitano, Tiziano Santilli.
`Large Language Models for Software Architecture Recovery from Source Code:
Class Diagrams, Patterns, Styles, and Architecture-as-Code Views`. SSRN, 2026.
DOI: [10.2139/ssrn.6381011](https://doi.org/10.2139/ssrn.6381011).
