# Evidence modes

The Architectural Evidence Constructor builds `evidence_pack.json`, which is the
single source of grounded technical information consumed by every downstream
agent. The pack is composed of six views:

| View | Source                                                                 |
|------|------------------------------------------------------------------------|
| A1   | Component diagram (textual / Mermaid)                                  |
| A2   | Component overview table                                               |
| A3   | API endpoints                                                          |
| A4   | Technology map                                                         |
| A5   | Dynamic interactions / sequence-style behaviour                        |
| A6   | Static class dependency / call graph                                   |

**A6 is always produced deterministically** by loading
`graph-artifacts/<system>-class-dependency.json` (already in the repository for
all four monoliths). **A1..A5 are configurable** via `--evidence-mode`.

---

## Mode 1: `llm` (default, recommended)

The agent calls the LLM with the chosen summarisation strategy (see
`--summarisation-strategy`) and prompts it to emit A1..A5 in a structured
format. Outputs are then normalised into `evidence_pack.json` and stable IDs
are minted.

**Pros:** self-contained run; consistent with how the previous paper produced
its artefacts; reproducible end-to-end inside the framework.

**Cons:** the most expensive option in tokens; subject to LLM nondeterminism.

```powershell
python -m agentic_decomposer run `
  --system jpetstore-6 `
  --evidence-mode llm `
  --summarisation-strategy 80k_concat
```

**Files written:**

```
01_evidence/
  evidence_pack.json
  raw_llm_views.json          # the LLM's raw structured output before normalisation
  summarisation_meta.json     # which strategy, token counts, model
```

---

## Mode 2: `deterministic`

The agent does **not** call the LLM for A1..A5. Instead it parses Java source
files (via `javalang`) and the static dependency graph to derive:

- **A2** component overview table — clusters classes by package and infers
  component type from class-name heuristics (`*Controller`, `*Service`,
  `*Repository`, `*Resource`, `*Servlet`, etc.).
- **A3** API endpoints — scans for Spring (`@RequestMapping`, `@GetMapping`,
  etc.), JAX-RS (`@Path`), and Servlet annotations and collects method/path/handler.
- **A4** technology map — reads `pom.xml`, `build.gradle`, `Dockerfile`,
  `docker-compose.yaml`, etc.

A1 (component diagram) and A5 (dynamic interactions) are emitted as empty views
in deterministic mode because they require synthesis beyond the static parser.

**Pros:** cheap, deterministic, fully grounded in code.

**Cons:** misses semantic richness in A1/A5; requires the parser to handle the
codebase correctly.

```powershell
python -m agentic_decomposer run `
  --system jpetstore-6 `
  --evidence-mode deterministic
```

**Files written:**

```
01_evidence/
  evidence_pack.json
  deterministic_views.json    # raw parsed structures before normalisation
```

---

## Mode 3: `external`

The agent loads pre-existing A1..A5 files from a user-provided directory.

Expected directory layout:

```
<external-views-dir>/
  <system>/
    A1.md              # component diagram, free-form text or Mermaid
    A2.json            # component overview table — list of {name, classes, type, responsibilities}
    A3.json            # API endpoints — list of {method, path, handler_class, related_entities}
    A4.json            # technology map — object {framework, database, build, ...}
    A5.md              # dynamic interactions, free-form text or scenarios list
```

If any file is missing, that view is set to `null` in the evidence pack. The
agent will **not** invoke the LLM as a fallback in `external` mode — that
behaviour is reserved for the `llm` mode.

**Pros:** lets you reuse A1..A5 from the previous paper or hand-curated views;
zero LLM cost for evidence.

**Cons:** the artefacts must exist; framework cannot reproduce them from scratch.

```powershell
python -m agentic_decomposer run `
  --system jpetstore-6 `
  --evidence-mode external `
  --external-views-dir ../old-paper-artifacts/architectural-views
```

**Files written:**

```
01_evidence/
  evidence_pack.json
  external_views_source.json  # records which files were loaded and their checksums
```

---

## Stable ID conventions

Whatever mode produces A1..A5, the Evidence Constructor mints **stable IDs**
that downstream agents must cite:

| Entity type        | ID prefix | Example       |
|--------------------|-----------|---------------|
| Component (A1/A2)  | `C`       | `C001`        |
| API endpoint (A3)  | `API_`    | `API_001`     |
| Scenario (A5)      | `S_`      | `S_001`       |
| Class node (A6)    | `K_`      | `K_001`       |
| Dependency edge (A6) | `E_`    | `E_001`       |

The A4 technology map is stored as a structured object in v1 and does not mint
separate `T_...` evidence IDs.

Domain capabilities (`BC001`, …) are minted later by the Domain Extractor
(⚠️ currently a placeholder — not yet concretized) and also referenced by
the Generator and Refiner.

---

## Choosing a mode for your experiment

| Goal                                              | Recommended mode |
|---------------------------------------------------|------------------|
| MVP / first end-to-end run                        | `llm`            |
| Cheapest pipeline for the four-system batch       | `deterministic`  |
| Reproducing the previous paper's exact evidence    | `external`       |
| Ablation: study the effect of LLM-inferred A1..A5  | run both `llm` and `deterministic` and compare downstream metrics |

See [ablation.md](ablation.md) for the design of the evidence-mode ablation.
