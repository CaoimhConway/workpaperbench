# Run your own workpaper evaluation

Run any of the 30 published tasks through native Harbor 0.23.0. The controller
can be your Linux workstation, dedicated server or VM. Docker Engine and Docker
Compose must run on that controller. Ubuntu 24.04 x86_64 is the validated platform.
The tested guest has six CPUs and 12 GiB RAM. Start with two concurrent trials.

## Direct Harbor execution

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Docker Engine](https://docs.docker.com/engine/install/) on the Linux controller,
then install the pinned harness:

```sh
uv tool install --python 3.12 'harbor==0.23.0'
```

Harbor downloads the task directories from the pinned release. Run all 30 oracle
solutions five times before evaluating a model in a new environment:

```sh
harbor run \
  --repo CaoimhConway/workpaperbench@v0.6.1-rc.1 \
  -p datasets/workflow-v9/tasks \
  --agent oracle -k 5 \
  --n-concurrent 2 --env docker
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
  --repo CaoimhConway/workpaperbench@v0.6.1-rc.1 \
  -p datasets/workflow-v9/tasks \
  --agent terminus-2 --model '<provider/model>' \
  --ak max_turns=24 \
  --n-concurrent 2 --env docker
```

Terminus-2 calls the model from the controller and sends terminal commands into
the candidate container. A custom Chat Completions endpoint must be reachable
from the controller. For example, with a server already running locally:

```sh
OPENAI_API_KEY=local-only harbor run \
  --repo CaoimhConway/workpaperbench@v0.6.1-rc.1 \
  -p datasets/workflow-v9/tasks -i c01 \
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

The [direct validation record](../reports/workflow-v9/direct-harbor-validation.json)
binds the oracle sweep and local scripted Terminus-2 fixtures. The fixtures check
native API transport, terminal feedback, retained delivery, positive and negative
grader outcomes, and isolation on development task `c01`. They make no inference
or provider calls and establish no model-performance result. To reproduce the
transport checks from a checkout of current `main`, run:

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

From a checkout of current `main` on the Linux Docker controller, run:

```sh
python3 scripts/workflow_regression.py \
  --output .local/my-workflow-regression.json
```

This checks the checkout's oracle solutions for `a01`, `b01`, `b02` and `c01`, followed
by correct and invalid scripted deliveries through native Terminus-2. It makes
no model calls. Missing diagnostics, infrastructure errors, changed artifacts
or unexpected rewards fail the command and remain in the result ledger. Use a
fresh output path. Raw native logs remain local beside the summary.
The [current recorded regression](../reports/workflow-v9/native-regression-v1.json) passed
all four oracles and both scripted deliveries without retries or inference.

The same command is available through the
[WorkpaperBench workflow regression](../.github/workflows/workflow-regression.yml)
manual GitHub Actions dispatch. It runs the current construction checks and
uploads their summary separately from historical reports.

## Configured Harbor/Hermes execution

The `wpb` interface below adds explicit endpoint-and-port restrictions, pinned
Hermes compatibility, identity-bound receipts and detailed financial reports.
It uses one tool-capable Chat Completions endpoint. No Mac, Lima, owner account,
environment marker or development-only permission is required.

The default `workflow-v9` construction track supplies source observations and an
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

git clone https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
git checkout v0.6.1-rc.1
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
./wpb grade --task c01 --artifacts examples/block-workpaper-v9 \
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
