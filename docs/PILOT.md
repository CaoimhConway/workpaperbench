# Preliminary difficulty pilot

Status: prepared but not executed. No provider compatibility, effective settings,
usage, latency, price, returned revision or model performance has been observed.
The prepared release `v0.6.3-rc.1` is unpublished. All commands use its local checkout,
`workflow-v11-canonical-99f9af5fc8cb`, scorer `workflow-1.2.1` and Harbor `0.23.0`.

This condition runs six development tasks once for provider compatibility and
initial usage/cost observation, then one attempt on each of the 24 evaluation
tasks per chosen frozen model configuration. The full [comparison](COMPARISON.md)
still uses three attempts per evaluation task. Pilot and comparison outcomes are
separate conditions. Do not add harder tasks before observing the pilot.

## Configure and freeze

Copy the [hosted-model template](../config/preliminary-hosted-model.example.json)
and [pilot manifest](../config/preliminary-pilot-manifest.example.json) to fresh
local files. Replace all angle-bracket placeholders and unresolved choices.
Choose the strong hosted model explicitly, without assuming a provider alias is
an immutable revision. Record actual request settings, effective limits and
sampling defaults where observable. Keep response model IDs when returned and
mark unavailable fields unknown. Never store credentials in these records.

Use the comparison's 24 turns, 3,600 agent seconds, 65,536 input context tokens,
requested 16,384 output tokens, high reasoning, JSON terminal parser, preserved
interleaved reasoning where required, Chat Completions, no summarization, fallback
or trial retries, and one concurrent attempt. Native request retries remain inside
the deadline and are recorded separately. Leave sampling unset. Reasoning may consume
the output budget. A provider that cannot support an option requires an explicit
configuration decision and separate identity. Inspect `harbor agent schema terminus-2`
and provider documentation before accepting the configuration. Never silently
remove or translate an unsupported setting.

The [local reference template](../config/preliminary-local-reference.example.json)
points to the historical local setup. Verify the loaded weights, quantization,
runtime and context rather than assuming those files describe a running server.
Resolve its reasoning placeholders explicitly and report a nonthinking setup as
a separate condition. Add the actual `api_base` for a controller-reachable endpoint.
No local inference is part of this preparation.

The harness does not enforce a monetary cap. Establish an explicit funded pilot
budget before launch, retain failed-call/cache/reasoning/retry costs where
observable, and record missing prices or usage as unknown. Existing owner spending
and execution restrictions still apply. These templates provide no spending or
inference authorization. Hash the resolved configuration and record the exact
checkout commit, catalog/scorer hashes, dependencies and image digests. After the
six development outcomes, freeze the final configuration and exact evaluation
schedule before opening any evaluation results. Retain development runs under
their actual configuration, even if compatibility requires a later change.

## Prepared inference commands - not executed

On the qualified Linux Docker controller, set provider credentials through its
supported environment variables. Create a unique campaign and matching manifest.
The Bash variables below must match the resolved configuration file. The manifest
is a ledger template for the existing Harbor jobs, not a second execution format.

```bash
model='<provider/strong-hosted-model>'
campaign='<unique-campaign-and-frozen-configuration-id>'
jobs_dir=".local/preliminary-pilot/$campaign"
recipe=(
  -p datasets/workflow-v11/tasks
  --agent terminus-2 --model "$model"
  --ak max_turns=24 --ak parser_name=json
  --ak enable_summarize=false --ak proactive_summarization_threshold=0
  --ak use_responses_api=false --ak reasoning_effort=high
  --ak interleaved_thinking=true
  --ak 'model_info={"max_input_tokens":65536,"max_output_tokens":16384}'
  --ak 'llm_call_kwargs={"max_tokens":16384}'
  --agent-timeout-multiplier 6
  --n-concurrent 1 --max-retries 0 --env docker
)

# First hosted-model smoke. PREPARED, NOT EXECUTED.
harbor run "${recipe[@]}" -i c01 -k 1 \
  --job-name "$campaign-smoke-c01-1" --jobs-dir "$jobs_dir"

# Inspect compatibility, files, verdict, usage and exceptions before continuing.
for task in a01 a02 b01 b02 c02
do
  harbor run "${recipe[@]}" -i "$task" -k 1 \
    --job-name "$campaign-smoke-$task-1" --jobs-dir "$jobs_dir"
done

# STOP here until the final configuration and evaluation schedule are frozen.
# Then run exactly once on each evaluation task. PREPARED, NOT EXECUTED.
tasks=(a03 a04 a05 a06 a07 a08 a09 a10
       b03 b04 b05 b06 b07 b08 b09 b10
       c03 c04 c05 c06 c07 c08 c09 c10)
for task in "${tasks[@]}"
do
  harbor run "${recipe[@]}" -i "$task" -k 1 \
    --job-name "$campaign-evaluation-$task-1" --jobs-dir "$jobs_dir"
done
```

Each Harbor trial has fresh candidate state and unique job/trial/output identities.
Retain every scheduled outcome, including failed delivery, timeout and infrastructure
error. Do not replace failures or tune on evaluation outputs. Record skipped or
unstarted slots explicitly if a budget or infrastructure interruption stops the pilot.

## Retain and report

Use the existing job `result.json`, trial `result.json`, retained workpaper and
`verifier/verdict.json`. Complete the manifest's 30 slots with their job/trial
paths and all outcomes. Retain configuration/artifact hashes, task/split/index,
actual request settings and returned IDs, start/finish times and latency, usage
including cache and reasoning, retries, exceptions, observable costs and unknowns.
Keep credentials out of configurations, receipts and shared artifacts. Inspect raw
logs before sharing. Native installed execution may expose its dedicated inference
key to candidate terminal tools. The separate verifier has no key or network.

Use the [efficient execution guide](RUNNING.md#efficient-execution-and-offline-analysis)
for immutable image preparation, optional provider cache settings, saved-artifact
analysis and continuation boundaries. Select and hash any routing changes before
launch. This pilot remains serial and retains every interrupted or failed slot.

Harbor reward is complete-workpaper completion. Report it alongside numerical
original tables, claim verdicts, evidence, changed-input robustness and delivery.
Show original and changed-input diagnostics separately and retain infrastructure
outcomes with unassessed financial dimensions. Do not infer missing usage or
costs from a zero reward. For saved artifact grading and the existing `wpb report`,
follow [external-agent integration](RUNNING.md#evaluate-your-own-agent). Regrading
is inference-free and must retain its own attempt identity and the original run.

Report all 24 evaluation tasks, the six development observations separately,
per-task failures and source-group limitations. One attempt supports an initial
difficulty observation, not a model ranking. Human review and external replication
remain pending. No pilot outcome is supplied by the authored software checks.
