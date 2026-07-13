# Metric engine integration

The framework does **not** re-implement Wang et al.'s metrics. It calls the
existing engine that already evaluates every baseline in `results/`. This
keeps numbers directly comparable to the previous paper and to all four agent
families already in this workspace.

---

## Where the engine lives

Same layout on Windows and Linux: the metric engine sits **one directory above
the workspace**, next to `agentic-experiments/`.

```
<shared parent>/
├── agentic-experiments/        ← this repository
│   └── agentic_decomposer/     ← this framework
└── src/
    └── metrics/
        └── scripts/
            └── evaluate_decomposition.py   ← the entry point we call
```

The framework resolves this path with `Path(__file__).resolve().parents[N]`,
**never with an absolute path**. This is the same convention used by
[scripts/calculate_metrics_paper_comparison.py](../../scripts/calculate_metrics_paper_comparison.py)
(`AGENTIC_DIR.parent / "src" / "metrics" / "scripts"`).

If the engine is not present at the expected location, the Evaluator agent
falls back to **emit-only mode**: it writes `decomposition.json` and a stub
`evaluation_report.json` containing only the local Quality Gate results, with
all metric fields set to `null`. A clear warning is logged. This lets the
framework run on a machine without the Java metric engine installed (for
example, on this Windows box during agent development) and have the metrics
computed later by syncing the run folders to the Linux box and running the
standard evaluator.

---

## How the engine is invoked

The Evaluator builds the same command line that
`calculate_metrics_paper_comparison.py` uses:

```bash
python  ../src/metrics/scripts/evaluate_decomposition.py \
  --application        <metrics_app>            \
  --granularity        class                    \
  --decomposition-file agentic_decomposer/runs/<run_id>/06_final/decomposition.json \
  --tool-name          agentic-<run_id>          \
  --output-format      json                      \
  --input-format       standard
```

`<metrics_app>` is the metric-engine name for the repo, which differs from the
codebase folder name:

| `--system` (codebase folder) | `--application` (metric engine) |
|------------------------------|---------------------------------|
| `demo`                       | `demo`                          |
| `jpetstore-6`                | `jpetstore`                     |
| `spring-petclinic`           | `spring-petclinic`              |
| `PartsUnlimitedMRP`          | `partsunlimited`                |

This mapping is encoded once in `agentic_decomposer.paths.REPO_TO_APP`.

---

## Java requirement

The metric engine needs a JRE on PATH. The existing
`calculate_metrics_paper_comparison.py` adds known Linux JRE directories
explicitly; this framework follows the same approach via
`agentic_decomposer.metrics.engine._java_env()`, with the candidate list
configurable through the `AGENTIC_DECOMPOSER_JAVA_HOMES` environment variable
(colon-separated on Linux, semicolon-separated on Windows).

If no Java is found, the engine call fails fast with a clear error; the
Evaluator then falls back to **emit-only mode** as described above.

---

## What metrics are produced

Output JSON from `evaluate_decomposition.py --output-format json` contains the
sections `turbomq`, `mojofm`, `entropy`, and `statistics`. The Evaluator pulls
the class-level row from each and maps them as follows (identical to
[scripts/calculate_metrics_paper_comparison.py](../../scripts/calculate_metrics_paper_comparison.py)):

| Framework metric key  | Engine source                                  |
|-----------------------|------------------------------------------------|
| `MoJoFM`              | `mojofm.Mojo`                                  |
| `CiD`                 | `100 - turbomq.CDP`                            |
| `CMod`                | `turbomq."Static Structural"`                  |
| `TC`                  | `turbomq.TurboMQ_contributors`                 |
| `LC`                  | `turbomq.TurboMQ_commits`                      |
| `DTP`                 | `entropy."Database Entropy"`                   |
| `DI`                  | `entropy."Use Case Entropy"`                   |
| `BCP`                 | `entropy."Sarah BCP"`                          |
| `num_services`        | `statistics."Actual Partition Count"`          |

These nine values populate `evaluation_report.json.metrics`. Any value missing
or returned as the sentinel `-1.0` is normalised to `null`.

---

## Granularity

The MVP runs only at **class** granularity, matching `baseline-1`..`baseline-5`
in this workspace. Method-level granularity (matching `baseline-6`..`baseline-10`)
is intentionally out of scope for the MVP; it will be added in V1 if the
class-level pipeline shows wins.

---

## Output location

When the engine writes its JSON output file, it lands under
`<METRICS_DIR>/output/<app>_<tool>_<timestamp>_results.json` (engine convention).
The Evaluator copies the relevant fields into
`agentic_decomposer/runs/<run_id>/04_evaluation/evaluation_report.json` and
stores a pointer to the original output file under each candidate result's
`engine_output_path` for traceability.
