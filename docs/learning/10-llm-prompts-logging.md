# 10 - LLM, Prompts, JSON Parsing, And Logging

This chapter covers the supporting machinery around LLM calls. The earlier
chapters explain the pipeline and agents; this one explains how prompts are
loaded, how model responses are parsed, how token usage is recorded, and how to
debug raw provider output.

## Why This Chapter Matters

In this framework, LLMs are allowed to reason, but they are not allowed to become
untraceable magic. Every LLM-backed agent follows the same discipline:

```text
build prompt from artifacts
call LiteLLM through one wrapper
parse strict JSON
validate against schema
write artifact
log prompt, response, token counts, and latency
```

That is the difference between an experiment and a loose chat workflow.

## The LiteLLM Wrapper

Open [LLMConfig](../../agentic_decomposer/llm/client.py#L14),
[LLMCallResult](../../agentic_decomposer/llm/client.py#L26), and
[LLMClient](../../agentic_decomposer/llm/client.py#L36).

The wrapper exists so agents do not call `litellm.completion` directly.

Reasons:

- one place to configure model, temperature, max tokens, and seed;
- one place to extract token counts across providers;
- one place to log every prompt and response;
- one future insertion point for retries, rate limits, or test doubles.

The actual call happens in [LLMClient.complete](../../agentic_decomposer/llm/client.py#L49).
Notice that `litellm` is imported inside the method. That means deterministic
code paths can import the framework without needing to call the LLM.

## Token And Latency Capture

Read [_extract_text_and_usage](../../agentic_decomposer/llm/client.py#L131).

LiteLLM normalizes provider responses toward an OpenAI-like shape, but usage
fields can still vary. The wrapper records:

```text
input_tokens
output_tokens
total_tokens
latency_ms
```

Those values become useful for RQ3-style practicality analysis: cost, runtime,
and stability.

## LLM Call Logging

Read [LLMClient._log_call](../../agentic_decomposer/llm/client.py#L91).

Each real run appends records to:

```text
agentic_decomposer/runs/<run_id>/logs/llm_calls.jsonl
```

Each line records:

```text
timestamp_utc
model
input/output/total tokens
latency_ms
system_prompt
user_prompt
response_text
```

Why JSONL?

- easy to append safely;
- easy to inspect one call at a time;
- easy to post-process into token/cost tables;
- avoids one giant JSON file that can be corrupted if a run stops early.

## Prompt Files

The prompt templates live in [prompts/](../../prompts/).

| Prompt | Used by | Purpose |
|--------|---------|---------|
| [evidence_views.md](../../prompts/evidence_views.md) | Evidence Constructor in `llm` mode | Ask for A1..A5 architectural views. |
| [domain_extractor.md](../../prompts/domain_extractor.md) | Domain Extractor ⚠️ (placeholder) | Infer capabilities, contexts, vocabulary, class mapping. > **⚠️ TEMPORARY PLACEHOLDER — NOT CONCRETIZED.** The Domain Knowledge
> Extractor is a bare placeholder (single LLM call + prompt). Planned for
> proper development in V2. Treat as temporary scaffold. |
| [generator_common.md](../../prompts/generator_common.md) | Generator | Shared candidate output contract and hard rules. |
| [generator_dependency_first.md](../../prompts/generator_dependency_first.md) | Generator | Strategy directive for low coupling and dependency structure. |
| [generator_domain_first.md](../../prompts/generator_domain_first.md) | Generator | Strategy directive for business capabilities and bounded contexts. |
| [generator_balanced.md](../../prompts/generator_balanced.md) | Generator | Strategy directive balancing dependency, domain, and migration concerns. |
| [refiner.md](../../prompts/refiner.md) | Refiner | Ask for controlled patch operations. |

Prompts are not hidden in code because prompt text is part of the research
method. Changing a prompt changes the experiment.

## Prompt Construction Pattern

Open [Generator prompt construction](../../agentic_decomposer/agents/decomposition_generator.py#L110).

The agent uses placeholder replacement:

```text
<<SYSTEM>>
<<STRATEGY>>
<<COMPONENTS_BLOCK>>
<<EDGES_BLOCK>>
<<CAPABILITIES_BLOCK>>
<<CLASSES_BLOCK>>
```

The helper functions at [generator context formatters](../../agentic_decomposer/agents/decomposition_generator.py#L266)
convert large artifacts into compact prompt blocks.

Why compact blocks?

- prompts must fit model context limits;
- LLMs need the most relevant evidence, not every raw file;
- compact formatting makes prompts readable in `llm_calls.jsonl`.

The Refiner follows the same idea. Open [Refiner prompt construction](../../agentic_decomposer/agents/decomposition_refiner.py#L115).

## Robust JSON Parsing

Open [extract_json](../../agentic_decomposer/helpers/json_parsing.py#L26).

LLMs often return:

```text
```json
{ ... }
```
```

or prose before/after JSON. The parser tries three strategies:

1. parse the whole response as JSON;
2. parse the first fenced code block;
3. scan for a balanced JSON object or array.

Then [extract_json_object](../../agentic_decomposer/helpers/json_parsing.py#L113)
requires the result to be a dictionary.

This parser is not permission for sloppy prompts. It is a safety net for common
provider formatting drift.

## Schema Validation After Parsing

Parsing JSON only proves the response is syntactically JSON. It does not prove
it has the right fields.

That is why agents then call [validate](../../agentic_decomposer/artifacts/validators.py#L32).

Example pipeline inside the Generator:

```text
LLM text
  -> extract_json_object
  -> normalize candidate
  -> validate candidate_decomposition schema
  -> write candidate_decompositions.json
```

## Logging Beyond LLM Calls

Open [logger.py](../../agentic_decomposer/logger.py#L1).

The framework logs at three levels:

| Log | Purpose |
|-----|---------|
| console rich logs | live progress while running. |
| `logs/controller.log` | run-level timeline. |
| `logs/agent_<name>.log` | per-agent detail. |
| `logs/llm_calls.jsonl` | raw prompt/response/token trace. |

Open [attach_file_handler](../../agentic_decomposer/logger.py#L52). The
controller and BaseAgent attach file handlers for the duration of a run or agent
call, then detach them. This avoids cross-run log leakage.

## Telemetry Setting

Open [disable_litellm_telemetry](../../agentic_decomposer/llm/client.py#L151).

This sets LiteLLM-related environment defaults to reduce unwanted provider
logging or telemetry. It is intentionally small and local.

## Debugging Raw LLM Failures

If an LLM-backed agent fails:

1. Open `logs/agent_<name>.log`.
2. Open `logs/llm_calls.jsonl`.
3. Copy the last `response_text` into a scratch file.
4. Check whether the response is valid JSON.
5. Check whether it matches the schema.
6. Check whether it hallucinated class names or evidence IDs.

For Generator failures, also open:

```text
03_candidates/schema_validation.json
```

That file records attempts and validation errors per candidate.

## Why Not Use Function Calling Everywhere?

The MVP uses strict JSON prompts plus schema validation because:

- it remains provider-portable through LiteLLM;
- it is easy to inspect in logs;
- schemas are already the artifact contract;
- provider-specific structured-output behavior can vary.

A future version could use provider-native JSON schema/function calling behind
`LLMClient.complete`, but it should still write the same artifacts.

## Checkpoint Questions

- Why do agents call `LLMClient` instead of LiteLLM directly?
- What is stored in `llm_calls.jsonl`?
- Why is JSON parsing separate from schema validation?
- Which files define the Generator's three strategies?
- Where would you add retry or rate-limit behavior later?

## Mini Exercise

Open [generator_common.md](../../prompts/generator_common.md#L1) and find the
hard rules. Then open [run_quality_gate](../../agentic_decomposer/metrics/quality_gate.py#L101).

Question:

```text
Which hard rules are enforced by prompt only, and which are checked by code?
```

That comparison is a good way to understand prompt engineering versus defensive
engineering.
