# Run your own workpaper evaluation

Run any of the 30 prepared construction tasks through native Harbor 0.23.0. The controller
can be your Linux workstation, dedicated server or VM. Docker Engine and Docker
Compose must run on that controller. Ubuntu 24.04 x86_64 is the validated platform.
The tested guest has six CPUs and 12 GiB RAM. Use one concurrent candidate trial
and at most two oracle trials. All inference examples in this guide are prepared
but not executed for workflow-v11.

## Direct Harbor execution

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Docker Engine](https://docs.docker.com/engine/install/) on the Linux controller,
then install the pinned harness:

```sh
uv tool install --python 3.12 'harbor==0.23.0'
```

The prepared release is `v0.6.3-rc.1`, not yet published. Use the exact local
checkout for every command below. Start with the [single-task quickstart](../README.md#quickstart).
Full qualification then runs all 30 oracle solutions five times before model evaluation:

```sh
harbor run \
  -p datasets/workflow-v11/tasks \
  --agent oracle -k 5 \
  --n-concurrent 2 --max-retries 0 --env docker
```

Each oracle attempt should have reward `1` and no exception. These are reference
checks, not model evaluations. Inspect the job's `result.json` and each trial's
`verifier/verdict.json`. A successful process exit alone does not establish that
the workpaper passed. Oracle solutions are available to the oracle agent, while
normal candidate images omit solutions, gold and verifier code.

For a model evaluation, provide the credentials required by the selected provider
through its environment variables and choose its Harbor model name:

```sh
harbor run \
  -p datasets/workflow-v11/tasks \
  --agent terminus-2 --model '<provider/model>' \
  --ak max_turns=24 \
  --n-concurrent 1 --max-retries 0 --env docker
```

Terminus-2 calls the model from the controller and sends terminal commands into
the candidate container. A custom Chat Completions endpoint must be reachable
from the controller. For example, with a server already running locally:

```sh
OPENAI_API_KEY=local-only harbor run \
  -p datasets/workflow-v11/tasks -i c01 \
  --agent terminus-2 --model openai/my-model \
  --ak api_base=http://127.0.0.1:8000/v1 \
  --ak 'model_info={"max_input_tokens":65536,"max_output_tokens":4096,"input_cost_per_token":0,"output_cost_per_token":0,"litellm_provider":"openai","mode":"chat"}' \
  --ak 'llm_call_kwargs={"max_tokens":4096}' \
  --ak temperature=0.6 \
  --ak max_turns=24 \
  --agent-timeout-multiplier 6 \
  --n-concurrent 1 --env docker
```

The placeholder above is for a credential-free local endpoint serving a
65,536-token context with a 4,096-token response limit. Replace both limits with
your server's actual configuration. `model_info` supplies the limits used for
Harbor's context accounting, while `llm_call_kwargs.max_tokens` sets the requested
response budget. Metadata does not configure the server. The zero cost fields
apply to this local example, not paid endpoints.

The task default allows 600 seconds of agent execution. This local example
multiplies that limit by six, allowing 3,600 seconds for a slower model server.
Choose and record a suitable wall-time budget before starting a comparison.

Supply any real key expected by an authenticated endpoint through the
corresponding provider environment variable. Declare sampling settings with
the agent's supported options. `harbor agent schema terminus-2` lists them.
Keep those settings and budgets fixed across a comparison and retain the job
configuration. The direct interface records the selected model name and options,
without attesting to the server's weights revision or enforcement of settings.

Use `-i c01` to select one development task. The complete development set is
`a01`, `a02`, `b01`, `b02`, `c01`, `c02`. To run only the 24 evaluation tasks, add:

```sh
-x a01 -x a02 -x b01 -x b02 -x c01 -x c02
```

The [comparison recipe](COMPARISON.md) fixes the agent, budgets and result metadata
for a declared comparison. The quickstart above is an execution example.

Use development tasks to select configurations before an evaluation comparison.
Set `--job-name` and `--jobs-dir` for identifiable new jobs. `-k` controls repeated
attempts, and `--n-concurrent` controls simultaneous trials. Keep failed attempts
and exceptions when interpreting coverage. Repeated attempts are not independent
tasks. Harbor's aggregate reward measures complete workpapers. The retained
verdict JSON separates numerical tables, claims, evidence, robustness and delivery.

### Agent and environment boundaries

Docker is the validated environment for these commands. Other Harbor agents
have their own setup, credentials and model options. Installed agents make API
calls inside the candidate environment and may expose their inference key to
terminal tools. Use a dedicated key with appropriate scope and spending controls.
Add `--allow-agent-host <provider-host>` when an installed agent needs an endpoint
beyond the task's default `172.17.0.1` allowlist.

Native Harbor applies that candidate host allowlist during execution. It permits
configured resolver DNS and ICMP, and uses a transparent proxy for TCP traffic.
A TCP connection to the proxy can succeed before an external destination is
rejected. The direct path does not enforce the configured `wpb` path's stricter
endpoint-and-port policy. Terminus-2's controller-side model calls are outside
the candidate network policy.

Verification runs in a fresh separate Docker environment with `network_mode:
none`, pristine observations, no inference key and no Docker socket. Its verifier records
check loopback-only interfaces and a failed external TLS probe. Read-only SQL
authorization and bounded workers constrain replay. These checks do not prove
security for arbitrary workloads. Modal and other sandbox backends have not been
validated against this verifier's network-namespace requirements.

The [release validation record](../reports/workflow-v11/README.md)
binds the oracle sweep and local scripted Terminus-2 fixtures. The fixtures check
native API transport, terminal feedback, retained delivery, positive and negative
grader outcomes, and isolation on development task `c01`. They make no inference
or provider calls and establish no model-performance result. To reproduce the
transport checks from the prepared checkout, run:

```sh
python3 scripts/validate_direct_harbor.py --checkout \
  --output .local/my-direct-harbor-validation.json
```

Use a fresh output path. Raw native logs stay below `.local` and need review before
sharing. The fixture explicitly injects a harmless test key into the candidate,
checks that terminal tools can read it, and verifies that the separate verifier
receives no key. This does not imply Terminus-2 forwards its real controller key.

A [local-model smoke record](../reports/workflow-v8/direct-model-smoke-v1/record.json)
and its retained workpaper exercise actual inference on the preserved
`workflow-v8` development task `b01` with Qwen3.6-35B-A3B, CPU inference and
native Terminus-2. The single attempt
completed nine turns and delivered all required files without an exception or
retry. Original-input calculations and claim verdicts passed. The complete reward
was `0` because claim 1 had no citations and the SQL failed changed-input controls:

- The queries did not deduplicate identical exports.
- The bridge multiplied a percentage-point difference by 10,000, producing a
  basis-point change 100 times too large when coverage changed.
- The reserve bridge used reported fair values instead of the specified reserve
  components, which diverged under the independent-disclosure control.

Inference used only a local endpoint, with zero external-service spend. This is
execution evidence from one development attempt, not a benchmark performance
estimate. The record includes weights, runtime, settings, file hashes and the
complete verifier diagnostics.

### Regression checks

From the prepared checkout on the Linux Docker controller, run:

```sh
python3 scripts/workflow_regression.py \
  --output .local/my-workflow-regression.json
```

This checks the checkout's oracle solutions for `a01`, `b01`, `b02`, `b06` and `c01`, followed
by correct and invalid scripted deliveries through native Terminus-2. It makes
no model calls. Missing diagnostics, infrastructure errors, changed artifacts
or unexpected rewards fail the command and remain in the result ledger. Use a
fresh output path. Raw native logs remain local beside the summary.
See the [current release validation](../reports/workflow-v11/README.md) for the exact checks completed and their retained identities.

To reproduce the corrected arithmetic, citation and SQL transport cases:

```sh
python3 scripts/validate_workflow_contract_revision.py \
  --output .local/my-contract-validation.json
```

The [contract validation record](../reports/workflow-v11/contract-validation.json)
includes accepted alternatives and rejected financial, citation and delivery
errors. These authored checks make no model calls.

The maintained regression command is also available through the
[WorkpaperBench workflow regression](../.github/workflows/workflow-regression.yml)
manual GitHub Actions dispatch. It runs the current construction checks and
uploads their summary separately from historical reports.

## Evaluate your own agent

Give your agent the task's `instruction.md` and only the files copied by its
`environment/Dockerfile`: `data.sqlite`, `sources.md`, `evidence.json`, `schema.json`
and `output_contract.json`. The permitted inputs for the example are in
`datasets/workflow-v11/tasks/c01/environment`. In the native candidate they are
at `/workspace`. Gold, solutions, tests and the checkout are outside that boundary.

Produce `answer.json` plus the three SQL basenames declared by the contract.
The [current example](../examples/block-workpaper-v11/answer.json) shows the JSON
schema and its adjacent SQL files. This authored reference is for integration
checking, not candidate input. Grade a saved artifact directory on the supported
Linux Docker controller, with fresh attempt IDs:

```sh
./wpb validate examples/block-workpaper-v11/answer.json
./wpb grade --dataset workflow-v11 --task c01 \
  --artifacts examples/block-workpaper-v11 --attempt external-reference-v11-1
./wpb report --attempts external-reference-v11-1 \
  --output .local/external-reference-v11-1-report.json

./wpb grade --dataset workflow-v11 --task c01 \
  --artifacts examples/block-frozen-ratio-v11 --attempt external-frozen-v11-1
./wpb report --attempts external-frozen-v11-1 \
  --output .local/external-frozen-v11-1-report.json
```

The reference passes. The negative fixture delivers valid files and citations,
and its original numbers pass. It reconstructs subscription cost using frozen
historical cost/revenue ratios. In `verifier.json`, `profit_bridge` has
`original: true` and `control_errors.subscription_cost_increases_with_matching_total:
"numeric"`. Delivery, claims and evidence pass, while robustness and complete
workpaper completion fail. Read the table diagnostics as well as the summary.
The [retained example reports](../reports/workflow-v11/README.md) demonstrate this
financial failure without a model. Replace `--artifacts` with your agent's saved
directory to use the same grading and reporting interfaces.

Structural validation is a smoke check. Oracle and negative qualification check
software behavior. Model-performance evaluation requires actual inference,
frozen configurations and all scheduled outcomes. Follow the
[preliminary pilot](PILOT.md) or the full [comparison protocol](COMPARISON.md).

## Configured Harbor/Hermes execution

The `wpb` interface below adds explicit endpoint-and-port restrictions, pinned
Hermes compatibility, identity-bound receipts and detailed financial reports.
It uses one tool-capable Chat Completions endpoint. No Mac, Lima, owner account,
environment marker or development-only permission is required.

The default `workflow-v11` construction track supplies source observations and an
output contract, with no starting SQL. Models write all three queries.
`--dataset workflow-v7` selects the separate maintenance track with supplied SQL
and repair/preservation reporting. Keep results from these conditions separate.

## 1. Install the native harness

Use Python 3.12, Docker Engine and the Docker Compose plugin. Ubuntu 24.04
x86_64 is the validated platform. Other Linux architectures are not rejected by
the runner, but have not been empirically validated. Allow about 12 GiB RAM and
40 GiB disk for runtime dependencies and images, plus resources for your model
server if it runs on the same machine.

Install Docker with [Docker's Linux instructions](https://docs.docker.com/engine/install/).
Run the controller and Docker daemon on the same Linux machine. Native Harbor
bind-mounts artifact and log paths, so a remote daemon with a different filesystem
is not supported by this setup. Docker client context, socket and TLS configuration
are preserved on the controller and are not injected into candidate environments.
Use a dedicated controller without unrelated credentials or sensitive host mounts.
Candidate tools execute inside Docker. The separate verifier has no network,
model access, inference credential or Docker socket. The controller retains the
checkout, references and Docker access outside the candidate.

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv
# Docker Engine and its Compose plugin must already be installed and usable.
docker info >/dev/null
docker compose version

# Transfer the exact prepared checkout to this controller, preserving its bytes.
cd /path/to/prepared/workpaperbench
# The proposed v0.6.3-rc.1 tag is not published.
python3 -m venv .venv
.venv/bin/pip install -e . harbor==0.23.0
mkdir -p .local
curl --fail --location \
  --header 'Accept: application/vnd.github.raw+json' \
  'https://api.github.com/repositories/1024554267/contents/scripts/install.sh?ref=8b66a51036c1e20920a17cdd049fdf55c968d683' \
  --output .local/hermes-install.sh
printf '%s\n' '25d3c95550e5ed7c0eec180a7d78dde765721c4e33639ab257c154c0a6e7554f  .local/hermes-install.sh' | sha256sum --check
./wpb preflight
```

Preflight checks Docker and the exact pinned native adapter. Runtime installation
downloads public dependencies before candidate egress is restricted. Bootstrap
dependencies are not fully locked. Setup failures remain infrastructure outcomes.
The historical Mac/Lima wrapper is available only through `./wpb local ...` and
is not part of this setup. `./wpb guest ...` remains an alias for the public commands.

## 2. Verify delivery and scoring without a model

```sh
./wpb grade --task c01 --artifacts examples/block-workpaper-v11 \
  --attempt reference-1
./wpb report --attempts reference-1 --output .local/reference-report.json
./wpb smoke --task c09 --attempt transport-1 --port 19090 --authenticated
```

The authored Block workpaper should pass every diagnostic and report three correct
queries on original inputs and controls. Construction has no repair or preservation
baseline. The smoke uses a local scripted endpoint, a test-only credential, two
scripted responses and a real Hermes terminal call. It deliberately delivers `{}`,
which the separate verifier rejects. Its transport proof is marked
`inference: false`, `financial_evaluation: false`. No model or provider is contacted.
The fixture discovers the Docker bridge for its listener. The chosen port must be
free, and `--host` can select a different controller address for the fixture.

## 3. Configure your model

Copy [the profile](../config/external-model.example.json) and edit the endpoint,
model ID, revision, serving runtime and budgets:

```sh
cp config/external-model.example.json .local/my-model.json
```

`serving.base_url` is the URL reachable from candidate containers, such as an
HTTPS team endpoint or an HTTP local model server. Arbitrary hostnames, addresses
and ports are accepted. A controller's `127.0.0.1` is not the candidate's loopback.
Bind or forward a local server to an address reachable from Docker, then put that
address in the profile. The runner does not install a provider proxy or require
`/models`. The endpoint must accept standard Chat Completions messages and tool
calls, including the native Hermes terminal tool.

For an authenticated endpoint, `serving.api_key_env` names the environment variable
containing its key. In a Bash shell, supply it without putting the value in a
profile, command argument or shell-history entry:

```sh
read -r -s -p 'Model API key: ' WPB_MODEL_API_KEY
export WPB_MODEL_API_KEY
```

For a credential-free local endpoint, remove `api_key_env`. The native client sends
the harmless `local-only` placeholder. HTTPS uses normal certificate verification
and the configured hostname. The runner resolves and pins endpoint addresses for
each trial and permits only that TCP destination and port, loopback, and necessary
local IPv6 neighbor discovery. Candidate DNS and unrelated outbound connections
are blocked. Use an endpoint that does not redirect to a different service.

The native installed client needs the inference key in its environment.
**Candidate terminal tools can read that key.** Use a dedicated key with appropriate
scope and spending controls. The verifier receives no key. Public profiles and
receipts record only its environment-variable name. Raw native traces remain
private and require review before sharing.

Model identity, weights revision and server enforcement of settings are declared
metadata. Record an immutable revision when available. If the server does not
report one, say `not reported by server` instead of inventing a pin. The harness
checks its native runtime revision, not your server's underlying weights.

The example sets 65,536 context tokens, 24 tool-loop turns, 4,096 generated tokens
per request and 3,600 candidate seconds. Set budgets suitable for your model and
use the same profile across a comparison. `max_tokens` is required. `temperature`,
`top_p` and `seed` are optional, so omit settings your server does not support.
Omitted sampling settings follow native client/server defaults. Hermes can make a final
request at its turn limit, so turns are not an exact request count. Setup has a
separate 1,200-second limit and verification has 180 seconds. No compression or
fallback model is enabled. The harness does not impose a monetary cap or claim
provider cost measurement. External inference cost is recorded as unknown.

## 4. Select and run tasks

```sh
./wpb list --split all
./wpb run --task c09 --profile .local/my-model.json --attempt my-model-c09-1
./wpb report --attempts my-model-c09-1 --output .local/my-model-c09-report.json

# Run all 24 evaluation cases with the same profile and fresh candidate state.
./wpb batch --split evaluation --profile .local/my-model.json --attempt my-model-eval-1
```

Both splits are runnable. Use `--split development` for six development cases,
`--split all` for all 30, or `--tasks a01 b01 c09` for an explicit batch.
The split describes experimental use, not an access restriction. Select your
profile on development cases before making an evaluation comparison.

A batch runs serially, creates attempt IDs such as `my-model-eval-1-c09`, and
retains each result plus `.raw/local-trials/my-model-eval-1-batch.json`. Failed
infrastructure attempts stay visible and cause a nonzero batch exit. Never reuse
an attempt ID. To report the batch, derive its explicit attempt list:

```sh
.venv/bin/python - <<'PY'
import json, subprocess
from pathlib import Path
batch = json.loads(Path('.raw/local-trials/my-model-eval-1-batch.json').read_text())
attempts = [row['attempt_id'] for row in batch['attempts']]
subprocess.run(['./wpb', 'report', '--attempts', *attempts,
                '--output', '.local/my-model-eval-1-report.json'], check=True)
PY
```

Use one native trial per installed harness environment. Independent workers need
separate Python environments and output directories. A new batch prefix always
starts fresh work. Previously completed attempts are not silently resumed.

To continue the same configured batch, repeat its exact arguments with `--resume`:

```sh
./wpb batch --split evaluation --profile .local/my-model.json \
  --attempt my-model-eval-1 --resume
```

The version 2 ledger binds task hashes, scorer, configuration bytes, execution
files, task order and serial concurrency. Resume retains successes, failures,
cancellations and interruptions. Only genuinely unstarted slots run. A start
marker without a receipt is `interrupted`, even if no candidate directory appeared.
Missing or altered recorded receipts and changed configurations are rejected.
Keep interrupted directories and ledgers. Those outcomes remain unassessed,
never zero-score answers or automatic replacement attempts. Intentional repetitions
need a new prefix and remain distinct attempts. Older ledgers cannot be resumed.
Proven runtime-lock contention stops dispatch before candidate creation and leaves
the slot explicitly `not_started_lock_busy`. Resume can dispatch it later. This
case is recorded separately from ambiguous starts and does not consume later slots.

## Read, replay and audit results

A zero process exit means the native run produced a receipt. Read the verdict to
see whether the workpaper passed. Reports include complete workpaper counts,
original/control-inclusive query correctness, evidence, claims, robustness,
delivery and infrastructure diagnostics. They state actual split coverage,
repeated tasks, and unknown costs. Missing delivery leaves financial outcomes
unassessed. Construction reports never borrow maintenance repair counts.

Exact submitted JSON is retained as `raw-answer.json`, normalized JSON as
`answer.json` when parseable, and SQL under `raw-sql/`, beneath
`.raw/local-trials/<attempt>/`. Receipts bind artifact, task, scorer and configuration
hashes. Reports reject mixed catalogs, tracks or model configurations, altered
verifier bytes and duplicate attempt IDs. Existing output files are never replaced.

For an inference-free replay, copy `raw-answer.json` to `answer.json` in a fresh
artifact directory and add the exact `raw-sql/*.sql` files. Run `./wpb grade
--dataset <original-catalog> --task <original-task> --artifacts <directory>
--attempt <new-id>`. Preserve the original receipt and catalog identity. Replays
and grader corrections do not become new model evaluations.

The [methods](WORKFLOW.md) include a portable all-task reference/control sweep.
The historical installed `workpaperbench` console entry point remains unchanged.
Use `./wpb` for this public interface.

## Efficient execution and offline analysis

The `execution-efficiency-1` setup reuses native infrastructure. Task instructions,
financial inputs, references, accepted alternatives, scoring and per-attempt
budgets remain the selected catalog's bytes. Record the checkout commit, profile
hash, native job `config.json` and `lock.json`, installed dependencies and image
identities before a comparison. Keep the frozen serial comparison unchanged.
Select any different routing or concurrency condition before starting a campaign.

### Immutable preparation

Install Harbor once on the controller and retain its dependency cache. Harbor
0.23.0 hashes Dockerfile contents, context files and modes, build arguments and
platform, and reuses content-addressed images under a build lock. Docker reuses
common base layers between tasks. Leave `force_build` false and keep the same
Docker daemon/cache. A cache hit still creates fresh writable candidate and
separate verifier containers. Never reuse candidate-modified filesystems.

The existing oracle qualification warms images without inference. For a small
setup measurement, run the same task twice under distinct job names:

```sh
harbor run -p datasets/workflow-v11/tasks -i c01 --agent oracle -k 1 \
  --n-concurrent 1 --max-retries 0 --env docker \
  --jobs-dir .local/setup-check --job-name first
harbor run -p datasets/workflow-v11/tasks -i c01 --agent oracle -k 1 \
  --n-concurrent 1 --max-retries 0 --env docker \
  --jobs-dir .local/setup-check --job-name warm
docker image ls --no-trunc --digests --format '{{json .}}' > .local/image-identities.jsonl
python -m pip freeze > .local/controller-dependencies.txt
./wpb analyze --jobs .local/setup-check/first .local/setup-check/warm \
  --output .local/setup-analysis.json
```

Call the first observation cold only if the relevant images were absent. Do not
delete caches to obtain that label. Setup includes container/network preparation
and does not isolate build time. The configured Hermes route downloads and checks
its installer once in `.local/hermes-install.sh`. Installation still occurs per
candidate and bootstrap dependencies are not fully locked. Current Terminus-2
comparisons already avoid that installed-agent bootstrap.

### Connections and caching

LiteLLM already caches SDK clients and HTTP transports. Hermes has its own native
client lifecycle. No pool, polling loop, request timeout, computation budget or
retry policy is replaced here. `--max-retries 0` disables trial retries, not all
request retries. Harbor 0.23.0 permits up to three attempts at each of its LLM-call
and Terminus query layers, in addition to SDK behavior. Retain observed retries
or unknowns. All waits and retries remain inside the original execution deadline.

For LiteLLM execution, add `"caching": false` to the existing `llm_call_kwargs`
object to disable full-response caching. This leaves provider prompt/KV caching
available. Every measured attempt must generate fresh responses. Keep messages,
tools and their order unchanged. IDs and timestamps belong in transport metadata.

The optional [OpenRouter example](../config/openrouter-execution.example.json)
uses existing Terminus-2 hooks. Resolve its endpoint slug and merge its
`llm_call_kwargs` into your frozen configuration. For one configured pilot job:

```bash
call_kwargs=$(python3 -c 'import json; print(json.dumps(json.load(open(".local/resolved-openrouter.json"))["llm_call_kwargs"]))')
harbor run "${recipe[@]}" -i c01 -k 1 \
  --ak "llm_call_kwargs=$call_kwargs" --ak "session_id=$attempt_id" \
  --jobs-dir "$jobs_dir" --job-name "$attempt_id"
```

`recipe`, `attempt_id` and `jobs_dir` are the frozen campaign values from the
[pilot](PILOT.md) or [comparison](COMPARISON.md). Assign a unique affinity ID per
attempt and retain it across that attempt's turns, outside messages. Pin one
endpoint with `provider.only` and disable fallback. Sticky affinity alone permits
fallback. `X-OpenRouter-Cache: false` disables full-response replay. Prompt caching
is capability-specific. Some endpoints cache automatically, others require
markers. Do not silently insert markers or substitute unsupported options during
a campaign. See OpenRouter's [prompt caching](https://openrouter.ai/docs/guides/best-practices/prompt-caching),
[provider selection](https://openrouter.ai/docs/guides/routing/provider-selection)
and [response caching](https://openrouter.ai/docs/guides/features/response-caching).
OpenRouter remains optional.

### Saved-artifact workflows

Native Harbor already supports inference-free regrading into a new job:

```sh
harbor job regrade .local/jobs/original-job \
  -p datasets/workflow-v11/tasks --env docker --n-concurrent 1 \
  --jobs-dir .local/regrades --job-name original-job-review-1
./wpb analyze --jobs .local/jobs/original-job \
  --output .local/original-job-analysis-1.json
```

Regrading uses the selected scorer and records `source_trial` provenance. Preserve
original results and workpaper bytes. Bind the selected catalog/scorer hashes
separately, especially when changing scorers. A regrade is analysis of an existing
attempt, never another model attempt. Use `./wpb grade` and `./wpb report` above
for standalone workpapers. Read native `verifier/verdict.json` or configured
`verifier.json` for original-input and changed-input diagnostics. These workflows
need no model credentials or inference.
Usage copied into a native regrade is labeled `inherited_model_metrics` and is
excluded from new-execution timing and token totals.

`./wpb analyze` reads local files without importing Harbor or contacting services.
Regenerate reports with fresh output filenames. It retains exceptions, interrupted
directories, unrecorded counts, configuration/lock hashes, declared execution
settings, returned model IDs and native timing/usage. New configured receipts also
retain these metrics. `wpb report` version `workpaper-1.3` adds coverage-aware
timing/token summaries and reads older receipts.

Prompt counts include cached tokens. Completion counts include reported reasoning
tokens. Neither subset is added again. Missing fields are `null`, not zero.
Native `cost_usd` can be a LiteLLM estimate and is labeled `reported_or_estimated`.
For saved OpenRouter response JSON, `--usage .local/response.json` extracts normal
usage fields and `usage.cost` in USD-denominated OpenRouter credits. That source
is never added to native totals or confused with credit-purchase fees.
Duplicate response IDs are rejected. Keep failed-call and retry usage where
available. Missing usage does not establish free calls. Review raw logs for keys
before sharing.

Request time comes from native request timers. Wall, setup, execution and verifier
time come from native timestamps. Tool execution and build-only time remain
unknown if not measured. Requested terminal wait durations are not measured tool
time. Reporting time measures this local analysis. Partial sums carry coverage.

### Concurrency and continuation

Harbor's `--n-concurrent N` uses independent conversations and writable containers.
Give any parallel condition a separate profile hash before launch. Keep each
task's CPU, memory, time and token limits. Provision the sum of active limits plus
controller, sidecar, verifier and model-server resources. Check rate limits and
contention before choosing N. The qualified six-CPU, 12-GiB controller retains
one model trial at a time. No parallel model profile is qualified here. The
configured `wpb` installed-agent route remains serial because its adapter and
environment setup are process-global.

Use `wpb batch --resume` for its configured ledger. For native pilot jobs, retain
every scheduled job identity and use the manifest to schedule only never-started
slots. Do not use default `harbor job resume` to erase interrupted outcomes:
Harbor 0.23.0 removes result-less trial directories and its CLI defaults to removing
cancelled trials. Preserve those outcomes and evidence. Do not restart the pilot
shell loop over existing job names.

At the next authorized provider smoke, retain actual request/response model and
endpoint IDs, cache reads/writes, reasoning usage, provider charges, failed calls
and request retries. Compare setup with recorded cache state, then request,
execution and verifier latency under the frozen deadline. The offline adapter and
scripted fixtures establish runner behavior, not hosted latency or cost savings.
