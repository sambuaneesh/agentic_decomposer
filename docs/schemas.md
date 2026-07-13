# Schemas

The artifact contracts that hold the framework together. Every JSON written or
read by an agent is validated against one of these schemas. If validation fails,
the controller fails the run rather than silently continuing with bad data.

The schemas live in [`../schemas/`](../schemas/) and are loaded by
`agentic_decomposer.artifacts.schemas.SchemaRegistry`.

---

## Schema list

| Schema file                              | Produced by                         | Consumed by                                  |
|------------------------------------------|-------------------------------------|----------------------------------------------|
| `run_config.schema.json`                 | CLI / config loader                 | Every agent (read-only)                      |
| `evidence_pack.schema.json`              | Evidence Constructor                | Domain Extractor, Generator, Evaluator, Refiner |
| `domain_model.schema.json`               | Domain Extractor                    | Generator, Refiner                           |
| `candidate_decomposition.schema.json`    | Generator, Refiner                  | Evaluator, Quality Gate, Process Controller  |
| `evaluation_report.schema.json`          | Evaluator                           | Refiner, Process Controller                  |
| `refinement_patch.schema.json`           | Refiner                             | Process Controller (audit), patcher          |
| `final_output.schema.json`               | Process Controller                  | Downstream analysis / experiment scripts     |

---

## Naming and ID conventions

- Service names are free-form strings; the Quality Gate enforces non-empty,
  unique-within-decomposition.
- Class IDs are **simple class names** (not fully-qualified). This matches the
  existing decomposition format used by every baseline in `results/`.
- Evidence IDs use stable prefixes (`C001`, `API_001`, `K_001`, ...). See
  [evidence_modes.md](evidence_modes.md#stable-id-conventions).
- Capability IDs use `BC001`, `BC002`, …

---

## Validation rules summary

The schemas enforce structural correctness only. Semantic correctness (e.g.
"every dependency points at a service that actually exists") is enforced by the
Quality Gate, not the schemas — see [`metrics/quality_gate.py`](../agentic_decomposer/metrics/quality_gate.py).

| Rule                                                          | Enforced by    |
|---------------------------------------------------------------|----------------|
| JSON is well-formed and has the required top-level keys       | JSON Schema    |
| Field types match (string, integer, array, …)                 | JSON Schema    |
| Required fields are present                                   | JSON Schema    |
| Enum values are within allowed sets                           | JSON Schema    |
| Every class is assigned exactly once                          | Quality Gate   |
| Every service has ≥1 class                                    | Quality Gate   |
| Every dependency target exists                                | Quality Gate   |
| Evidence references point at IDs that exist in evidence_pack/domain_model | Quality Gate   |
| No cyclic dependency above configured threshold               | Quality Gate (warning, not error) |

---

## Versioning

Every schema has a `$id` of the form `https://agentic-decomposer/schemas/<name>/v1.json`.
Bumping a schema is a breaking change for downstream agents and requires:

1. New file `<name>.schema.v2.json` (keep v1 for backward compatibility).
2. Update `SchemaRegistry` to prefer v2 unless `--schema-version 1` is passed.
3. Note the change in [`changelog.md`](changelog.md) (created once the first
   schema change happens — file is intentionally absent until then).
