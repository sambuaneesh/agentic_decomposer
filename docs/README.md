# Documentation Index

Start here if you are browsing the documentation folder directly.

## Best Starting Point For A New Reader

Open [learning/README.md](learning/README.md).

That guided track teaches the project from zero to ownership. It explains the
research motivation, repository structure, artifact contracts, controller flow,
agents, metrics, experiments, extension paths, and debugging strategy.

## Linear Learning Track

| Order | File | Use it for |
|-------|------|------------|
| 0 | [learning/README.md](learning/README.md) | Main syllabus and reading route. |
| 1 | [learning/01-research-context.md](learning/01-research-context.md) | Old paper, Wang et al., and new claim. |
| 2 | [learning/02-repository-map-and-entrypoints.md](learning/02-repository-map-and-entrypoints.md) | Folders, CLI, config, paths, run layout. |
| 3 | [learning/03-artifact-contracts.md](learning/03-artifact-contracts.md) | JSON schemas and artifact flow. |
| 4 | [learning/04-controller-and-run-lifecycle.md](learning/04-controller-and-run-lifecycle.md) | Process Controller and complete run sequence. |
| 5 | [learning/05-agents-deep-dive.md](learning/05-agents-deep-dive.md) | Each agent's role, inputs, outputs, and code. |
| 6 | [learning/06-metrics-quality-and-refinement.md](learning/06-metrics-quality-and-refinement.md) | Metrics, Quality Gate, composite score, Refiner. |
| 7 | [learning/07-experiments-and-results.md](learning/07-experiments-and-results.md) | MVP, all-system, and ablation experiments. |
| 8 | [learning/08-extension-playbook.md](learning/08-extension-playbook.md) | How to extend the framework safely. |
| 9 | [learning/10-llm-prompts-logging.md](learning/10-llm-prompts-logging.md) | LLM wrapper, prompt templates, JSON parsing, and logging. |
| 10 | [learning/11-source-file-index.md](learning/11-source-file-index.md) | File-by-file source tree ownership index. |
| 11 | [learning/12-next-versions-roadmap.md](learning/12-next-versions-roadmap.md) | Post-MVP V1/V2/V3 roadmap after initial Linux testing. |
| 12 | [learning/13-literature-gap-analysis.md](learning/13-literature-gap-analysis.md) | Literature scan, gap analysis, and research-priority plan. |
| Ref | [learning/09-glossary-and-debugging.md](learning/09-glossary-and-debugging.md) | Glossary, symptom-based debugging, Linux checklist. |

## Reference Docs

Use these after the learning track or when you already know what you need:

| File | Purpose |
|------|---------|
| [architecture.md](architecture.md) | Concise architecture and design rules. |
| [usage.md](usage.md) | Installation, CLI flags, configs, outputs. |
| [evidence_modes.md](evidence_modes.md) | `llm`, `deterministic`, and `external` evidence behavior. |
| [schemas.md](schemas.md) | Schema list and validation policy. |
| [metric_engine.md](metric_engine.md) | Integration with the sibling Wang-style metric engine. |
| [ablation.md](ablation.md) | Variant definitions and interpretation. |
| [mvp_roadmap.md](mvp_roadmap.md) | Build status and no-API verification record. |
| [learning/12-next-versions-roadmap.md](learning/12-next-versions-roadmap.md) | Detailed next-version planning after MVP testing. |
| [learning/13-literature-gap-analysis.md](learning/13-literature-gap-analysis.md) | Literature-grounded gaps and what to work on next. |

## Suggested Teaching Flow

If explaining the project to someone else:

1. Spend 10 minutes on the old-paper motivation in the learning track.
2. Draw the artifact chain on a whiteboard.
3. Open `ProcessController.run` and trace one execution.
4. Open one agent at a time, always asking: input, output, validation, failure.
5. Finish with the ablation grid and ask what result would support or weaken the
   agentic-framework claim.
