# Experimental financial reasoning tier

`workflow-hard-pilot-v1` contains three construction tasks, all marked development. It starts from checkout `c9afff4ba933ff3bb98e5357818ac20aff4eb052` and retains the workflow-v15 four-file delivery interface, frozen `workflow-1.2.1` scorer and isolated verifier. No model results establish that these tasks are harder. The completed GLM pilot motivates the investigation, not task selection against a model family or a target pass rate.

| Task | New financial work | Closest existing coverage |
| --- | --- | --- |
| [a01: Ahold Delhaize](../datasets/workflow-hard-pilot-v1/tasks/a01/instruction.md) | Reconstruct comparable sales across merger perimeter, divestments, reinstated calendar days and a nonuniform extra week. Derive pre-Q4 periods and a signed annual presentation bridge. | c07 identifies publication changes and unequal acquisition durations. a03 subtracts cumulative periods on one reporting basis. This task requires an actual comparable numerical result across several bases. |
| [b01: Microsoft](../datasets/workflow-hard-pilot-v1/tasks/b01/instruction.md) | Separate capital cash outlay from payable-adjusted purchase proxies and noncash lease recognition. Reconcile total and nested finance-lease assets, preserving unallocated differences. | a07 constructs cash generation, and b10 reconciles earnings to cash. Neither requires this cash-to-gross/net-asset bridge with principal versus recognition and nested depreciation scope. |
| [c01: Apple](../datasets/workflow-hard-pilot-v1/tasks/c01/instruction.md) | Infer sharp exposure and stress-loss bounds from separate category and country marginals. Optimize revenue and gross profit separately and establish endpoint feasibility. | c01 leaves a causal quantity unresolved. c10 transforms a supplied forecast range. This task derives an interval from joint-allocation constraints, with different optimal allocations for two objectives. |

The dossier supplies compact factual tables, authentic definitions, dates, periods and units. It does not supply starting SQL or the requested worked derivations. Apple's stress rates and constant category-margin assumption are explicitly authored. Microsoft's purchase proxy and depreciation-scope convention are identified as analytical definitions. Ahold's comparison retains reported FX and different former-business calendars, and is not labelled organic growth.

Source mappings and worked references are available for [Ahold](../datasets/workflow-hard-pilot-v1/references/a01.md), [Microsoft](../datasets/workflow-hard-pilot-v1/references/b01.md) and [Apple](../datasets/workflow-hard-pilot-v1/references/c01.md). Each package has an executable `solution/solve.sh`, three reference queries, an `alternative/` four-file submission and hidden changed-input databases. The builder binds task trees, source extracts, scorer and SQL worker to the [manifest](../datasets/workflow-hard-pilot-v1/manifest.json).

Only attributed factual extracts and short definitions are retained. Full issuer reports are not redistributed. Source-extract hashes are distinct from original-document hashes. Apple's original downloaded HTML hash is retained. Ahold and Microsoft have retained-extract hashes and precise primary-source locators, without claiming an uncaptured original-document hash. The [redistribution policy](../DATA_SOURCES.md) applies.

## Execution and verification

No scoring extension is needed. The only existing-runtime changes register the explicit new dataset and apply the existing materialization-integrity environment to it. Baseline packages, publication bindings, scorers, historical results and campaigns retain their identities.

From a supported Ubuntu 24.04 Docker controller with the documented runtime, use these inference-free checks. New report and attempt identities must not already exist.

```sh
python scripts/build_workflow_hard_pilot.py --check
python -m pytest -q tests/test_workflow_hard_pilot.py
python scripts/validate_workflow_hard_pilot.py \
  --output .local/hard-verification.json --native-prefix hard-verification
```

To replay an alternate workpaper through the supported path:

```sh
./wpb grade --dataset workflow-hard-pilot-v1 --task c01 \
  --artifacts datasets/workflow-hard-pilot-v1/tasks/c01/alternative \
  --attempt hard-apple-alternative
```

The final [verification record](../reports/workflow-hard-pilot-v1/README.md) reports accepted alternatives and rejected analytical mistakes. The independent reference checks include Ahold's extra-week cancellation, Microsoft's gross-versus-accumulated asset derivation, and feasible Apple allocations with an exchange optimality certificate. These support the economic formulas as well as the arithmetic.

Controls test relevant operands and invariances. Claims remain scoped to the original dossier, while SQL reruns on every control. Optional explanatory prose and sharpness proofs are not semantically verified. No arbitrary witness is exact-matched. All supplied evidence is compact and relevant, so additional known dossier context is accepted with sufficient core support. Unknown citations and missing core support fail.

## Calibration recipe, not executed

The [machine-readable recipe](../config/workflow-hard-pilot-v1-calibration.json) schedules one fresh attempt per task for the existing GLM-5.3 high-reasoning Wafer condition and one proposed strong reference condition. The reference model is Claude Opus 5.5 at requested high effort. Its exact provider, Harbor route, serving revision and parameter translation remain unresolved and must be frozen before use. The [provider's model documentation](https://platform.claude.com/docs/en/models/opus-5-5/overview) establishes the model identity, not compatibility with the pinned native runtime.

Both conditions retain 3600 candidate seconds, 24 turns, 65536 input-context metadata and 16384 output tokens including reasoning per request, with one concurrent trial, zero whole-trial retries, fresh state and no summarization. Task TOML retains the baseline 600-second base, multiplied by six in qualified model execution. Oracle replay uses its existing separate bounded oracle execution, not a candidate-model budget. Native within-request retries and output-limit recovery retain their qualified behavior and must be included in usage records.

After a provider and execution freeze, the GLM native command template is below. It is prepared, not executed. Each `slot` must be unique, and the exact source/catalog hash must match the checkout. The reference condition uses the same budgets with its resolved provider options, rather than inheriting GLM routing fields.

```bash
task=a01
slot='<unique-hard-development-slot>'
manifest='<frozen-workflow-hard-pilot-v1-manifest-id>'
controller='<absolute-isolated-controller-checkout>'
harbor run -p datasets/workflow-hard-pilot-v1/tasks -i "$task" -k 1 \
  --agent terminus-2 --model openrouter/z-ai/glm-5.3 \
  --ak max_turns=24 --ak parser_name=json \
  --ak enable_summarize=false --ak proactive_summarization_threshold=0 \
  --ak use_responses_api=false --ak reasoning_effort=high \
  --ak interleaved_thinking=true --ak store_all_messages=true \
  --ak 'model_info={"max_input_tokens":65536,"max_output_tokens":16384,"supports_reasoning":true}' \
  --ak 'llm_call_kwargs={"max_tokens":16384,"caching":false,"extra_headers":{"X-OpenRouter-Cache":"false"},"extra_body":{"provider":{"only":["wafer/us"],"allow_fallbacks":false,"require_parameters":true}}}' \
  --ak "session_id=$slot" --agent-timeout-multiplier 6 \
  --n-concurrent 1 --max-retries 0 \
  --env workpaperbench.runtime_integrity:VerifiedDockerEnvironment \
  --ek "canonical_root=$controller" --ek "expected_manifest=$manifest" \
  --ek "expected_task=workflow-hard-pilot-v1-$task" \
  --job-name "$slot" --jobs-dir .local/hard-calibration/jobs
```

Repeat under the frozen schedule for b01 and c01. Obtain separate authorization before model calls or spending. Retain failures, limits, all observable usage and missing fields. The inference credential follows the selected native route and is not guaranteed inaccessible to candidate terminal tools. The separate verifier has no credential or network.

These are three development cases, including issuer overlap with historical suites. They are not a held-out evaluation set or a contamination-free sample. Human financial/source review, external-user validation, empirical difficulty and reference-provider qualification remain pending. The completed software verification is not evidence of model performance.
