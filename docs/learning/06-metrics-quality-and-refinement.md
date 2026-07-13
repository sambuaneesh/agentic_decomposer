# 06 - Metrics, Quality, And Refinement

This chapter explains the feedback loop: how candidates are measured, how local
quality is enforced, and how refinement changes a candidate.

## Three Different Notions Of Good

The framework separates three meanings of "good":

| Layer | Question | Implemented where |
|-------|----------|-------------------|
| Wang metrics | Does the candidate score well against benchmark metrics? | [metric engine wrapper](../../agentic_decomposer/metrics/engine.py#L87) |
| Local quality | Is the candidate structurally valid and grounded? | [quality gate](../../agentic_decomposer/metrics/quality_gate.py#L101) |
| Internal selection | Which candidate should the controller try next? | [composite score](../../agentic_decomposer/metrics/composite_score.py#L33) |

Do not collapse these into one number. The paper should report individual
metrics. The composite score is only for controller decisions.

## Metric Engine Wrapper

Open [run_metric_engine](../../agentic_decomposer/metrics/engine.py#L87).

The wrapper calls the existing external metric engine:

```text
../src/metrics/scripts/evaluate_decomposition.py
```

It passes:

```text
--application <metric-app-name>
--granularity class
--decomposition-file <candidate decomposition json>
--tool-name <agentic tool name>
--output-format json
--input-format standard
```

Why wrap instead of reimplement?

- Keeps numbers comparable with the previous paper.
- Avoids redefining Wang metrics accidentally.
- Lets B0 and agentic outputs share the same scoring path.

Open [extract_metrics](../../agentic_decomposer/metrics/engine.py#L236). That is
where raw engine output becomes the framework metric keys.

## Emit-Only Mode

The Evaluator can still complete if the metric engine is missing. It writes
metrics as `null` and logs a warning.

This is useful on a development laptop where Java or the sibling metric engine
is unavailable. It is not the final paper path. On Linux, the sibling metric
engine should be present.

## Local Quality Gate

Open [QualityGateResult](../../agentic_decomposer/metrics/quality_gate.py#L33)
and [run_quality_gate](../../agentic_decomposer/metrics/quality_gate.py#L101).

The gate checks problems that are easier to reason about locally than through
benchmark metrics:

```text
assignment coverage
duplicate class assignment
empty services
unique service names
valid simple class names
dependency targets
self dependencies
responsibility text
evidence references
reference ID validity
service count bounds
cycle count
```

Cycle count is recorded, but the gate does not automatically reject every cycle.
That is important because cyclic independence is already a metric story through
CiD. The gate primarily blocks invalid shapes.

## Evidence Reference Validation

The quality gate does more than require non-empty `evidence_refs`. It checks
that each cited ID exists in the current evidence or domain artifacts.

Open [known reference IDs](../../agentic_decomposer/metrics/quality_gate.py#L225).

Valid citations can come from:

```text
classes: K_...
components: C...
api_endpoints: API_...
dependency_edges: E_...
dynamic_interactions: S_...
business_capabilities: BC...
```

This makes the Generator accountable. A service cannot simply cite imaginary
`BC999` evidence and pass the gate.

## Composite Score

Open [compute_composite_score](../../agentic_decomposer/metrics/composite_score.py#L33).

The composite score is internal. It combines objective weights from `RunConfig`
with available metric values. If the quality gate fails, the score is penalized.

Why use it at all?

The Evaluator may need to choose among multiple candidates. A scalar tie-breaker
is useful for orchestration, but paper analysis should still report the raw
metrics.

## Evaluation Diagnostics

Open [diagnostic builder](../../agentic_decomposer/agents/decomposition_evaluator.py#L196).

Diagnostics translate quality and metric problems into messages the Refiner can
act on:

```text
duplicate_class
missing_class
invalid_class_name
missing_evidence_ref
invalid_evidence_ref
service_count_out_of_bounds
cyclic_dependency
low_domain_independence
low_business_context_purity
low_modularity
```

Then open [recommendation logic](../../agentic_decomposer/agents/decomposition_evaluator.py#L273).

The recommendation is one of:

```text
accept
refine
reject
```

Hard structural failures reject a candidate. Softer metric or cycle issues can
ask for refinement.

## Refinement Operations

Open [operations.py](../../agentic_decomposer/refinement/operations.py#L14).

The operation set is deliberately small:

| Operation | Meaning |
|-----------|---------|
| `move_class` | Move one class between services. |
| `split_service` | Split one service into named smaller services. |
| `merge_services` | Merge source services into a target service. |
| `rename_service` | Rename a service and update dependencies. |
| `add_dependency` | Add a service dependency. |
| `remove_invalid_dependency` | Remove a problematic dependency. |
| `reassign_responsibility` | Move or add a responsibility statement. |

This gives the Refiner enough vocabulary to make local repairs without allowing
it to erase the initial candidate and start over.

## Deterministic Patching

Open [apply_patch](../../agentic_decomposer/refinement/patcher.py#L34).

The patcher is deterministic and defensive:

- unknown operations are skipped;
- invalid moves are skipped with an audit message;
- valid operations are applied to a deep copy;
- applied and skipped operations are written in refined candidate metadata.

Read handlers like [move class handler](../../agentic_decomposer/refinement/patcher.py#L74)
and [split service handler](../../agentic_decomposer/refinement/patcher.py#L90).

Why not let the LLM directly edit JSON?

Because controlled patching lets the experiment answer:

```text
What exactly changed after evaluation feedback?
```

## Refinement Selection

The controller re-evaluates the refined candidate. Then it only selects the
refined candidate if the report improves.

Open [improvement check](../../agentic_decomposer/agents/process_controller.py#L172).

The improvement rule considers recommendation status and composite score. This
prevents a lower-quality refined candidate from replacing a better initial one.

## Example Feedback Loop

A possible cycle-breaking story:

```text
Generator creates CAND_001.
Evaluator finds cyclic dependency between OrderService and PaymentService.
Evaluation report recommends refinement.
Refiner emits remove_invalid_dependency or move_class.
Patcher applies the local operation.
Evaluator re-scores CAND_001_REFINED_1.
Controller selects refined candidate only if improved.
```

A possible domain-alignment story:

```text
Evaluator reports low DI or BCP.
Refiner sees domain capabilities and class-capability matrix.
Refiner moves or splits classes by bounded context.
Quality Gate verifies no class was lost or duplicated.
```

## Checkpoint Questions

- Why does the framework need both Wang metrics and a local Quality Gate?
- Why is the composite score not a publishable result by itself?
- What happens when the metric engine is missing?
- Why is a patch better than free-form regeneration for refinement analysis?
- Which operation would you use for an oversized service?
- Which operation would you use for a fake dependency target?

## Mini Exercise

Create a tiny mental candidate with two services and one duplicate class. Predict:

- which quality field fails;
- which diagnostic appears;
- whether recommendation is accept, refine, or reject;
- which refiner operation could fix it.

Then verify by reading [duplicate class diagnostic](../../agentic_decomposer/agents/decomposition_evaluator.py#L202).
