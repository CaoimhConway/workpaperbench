# Model comparison protocol

Use this recipe to evaluate models under one declared construction condition.
The [configuration template](../config/construction-comparison-v15.json) fixes the
task, scorer, agent and resource settings. It contains no model results.

The [v15 software checks](../reports/workflow-v15/README.md) cover selected
references and native scripted delivery. The [earlier comparison validation](../reports/workflow-v11/comparison-recipe-validation.json)
checked budget and reasoning forwarding on v11. It is historical evidence, not
validation of this v15 recipe. Before inference, run the scripted check below on
your Linux controller. It makes no model calls and does not establish provider
compatibility or performance.

```sh
export PYTHONPATH="$PWD"
python3 scripts/validate_direct_harbor.py --checkout \
  --comparison-recipe config/construction-comparison-v15.json \
  --output .local/my-comparison-recipe-validation.json
```

## Freeze the configuration

Use Harbor 0.23.0 from this checkout with catalog
`workflow-v15-canonical-400f60b5b3b6` and scorer `workflow-1.2.1`. Complete the
[environment and oracle checks](RUNNING.md#direct-harbor-execution) first.

Before any model calls, save a separate configuration for each model with its
exact provider, requested model revision, policy for recording returned model
identifiers, serving backend and version, quantization when applicable,
dependency versions, image digests and configuration hash. Resolve aliases where
the provider permits it. Record an unversioned endpoint as such and retain
response model identifiers.

The fixed budget is 24 turns, 3,600 agent seconds, 65,536 input tokens for context
accounting and a requested 16,384 output tokens per call. Record the provider's
effective context and output limits, including how reasoning consumes them.
Model metadata does not configure a server or prove that it enforces a limit.

The [efficient execution guide](RUNNING.md#efficient-execution-and-offline-analysis)
covers native image/client reuse, provider-specific prompt caching, saved-artifact
analysis and honest continuation. Optional routing or concurrency changes require
a separate frozen condition. This recipe's serial settings remain unchanged.

Use high reasoning, JSON terminal parsing, Chat Completions and preserved
interleaved reasoning where required. Disable summarization and model fallback.
Leave sampling parameters unset and record the effective provider defaults and
any settings that cannot be observed. An unsupported option or changed provider
behavior requires a distinct configuration identity and disclosure of the
different condition. Do not silently substitute settings or pool those results.

Supply provider credentials through its supported environment variables. Retain
usage and costs for failed calls, cache operations, reasoning and retries.
The harness does not enforce a monetary cap. Mark unobserved costs as unknown.

## Run the smoke and comparison stages

All inference commands below are prepared but not executed. The following Bash
recipe uses Terminus-2 through LiteLLM Chat Completions.
Replace the model placeholder after freezing its configuration. Choose a fresh
job name and output directory for every execution.

```bash
model='<provider/model>'
jobs_dir='.local/comparison/<frozen-model-configuration-id>'
export PYTHONPATH="$PWD"
recipe=(
  -p datasets/workflow-v15/tasks
  --agent terminus-2 --model "$model"
  --ak max_turns=24 --ak parser_name=json
  --ak enable_summarize=false --ak proactive_summarization_threshold=0
  --ak use_responses_api=false --ak reasoning_effort=high
  --ak interleaved_thinking=true
  --ak 'model_info={"max_input_tokens":65536,"max_output_tokens":16384}'
  --ak 'llm_call_kwargs={"max_tokens":16384}'
  --agent-timeout-multiplier 6
  --n-concurrent 1 --max-retries 0 \
  --env workpaperbench.runtime_integrity:VerifiedDockerEnvironment
  --ek canonical_root="$PWD"
  --ek expected_manifest=workflow-v15-canonical-400f60b5b3b6
)

# First smoke task checks provider compatibility and retained artifacts.
harbor run "${recipe[@]}" -i c01 -k 1 \
  --ek expected_task=workflow-v15-c01 \
  --job-name smoke-c01 --jobs-dir "$jobs_dir"

# Continue once each on the remaining development tasks after checking c01.
for task in a01 a02 b01 b02 c02
do
  harbor run "${recipe[@]}" -i "$task" -k 1 \
    --ek expected_task="workflow-v15-$task" \
    --job-name "smoke-$task" --jobs-dir "$jobs_dir"
done

# Freeze the final configuration before opening evaluation results.
tasks=(a03 a04 a05 a06 a07 a08 a09 a10
       b03 b04 b05 b06 b07 b08 b09 b10
       c03 c04 c05 c06 c07 c08 c09 c10)
for task in "${tasks[@]}"
do
  for attempt in 1 2 3
  do
    harbor run "${recipe[@]}" -i "$task" -k 1 \
      --ek expected_task="workflow-v15-$task" \
      --job-name "evaluation-$task-$attempt" --jobs-dir "$jobs_dir"
  done
done
```

The smoke stage covers six development tasks once each and supports compatibility
checks, not ranking. The comparison stage is 72 attempts per model across the
24 immutable evaluation tasks. Each attempt starts a fresh session and candidate
environment. Use the same frozen task order and attempt schedule for every model.
Retain all outcomes, including failures, timeouts and infrastructure errors.
Do not replace unsuccessful attempts with retries or tune on evaluation outputs.

## Retain and report

Keep the frozen configuration, source and artifact hashes, job and trial IDs,
task IDs and split, attempt index, actual request settings, returned model IDs,
start and finish times, exceptions, retry counts, token usage, cache usage,
costs, workpapers and separate-verifier verdicts. Review raw logs for credentials
before sharing them.

Report complete-workpaper reward alongside financial-answer, numerical-table,
claim-verdict, evidence, robustness and delivery outcomes. Unassessed dimensions
remain unassessed. Show original-input and changed-input diagnostics separately.
Report per-task variation and uncertainty at the task or source-group level.
Repeated attempts on one task do not increase the number of independent tasks.
This sample supports bounded comparisons and does not establish a general model
ranking. Keep historical runs with different agents, quantization, reasoning,
sampling or budgets in their original conditions.

## Historical protocols

The [v11 comparison template](../config/construction-comparison.json) and
[preliminary difficulty pilot](PILOT.md) retain their original catalog and
conditions. The pilot uses one attempt per evaluation task. This v15 comparison
uses three attempts per evaluation task, 72 outcomes per model. Keep their
results separate. To check the historical comparison settings, pass
`--comparison-recipe config/construction-comparison.json` with `--checkout` to
the scripted validator.
