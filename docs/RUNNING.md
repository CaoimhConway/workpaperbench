# Run your own workpaper evaluation

Use the existing Harbor 0.23.0 / Hermes harness directly inside a dedicated
Ubuntu 24.04 x86_64 guest. This path needs no Mac, Lima, owner account, model
weights path or hosted provider integration. Docker runs inside the guest.

The guest must have no shared host folders, private credentials, forwarded SSH
agent or unrelated workloads. The repository stays on the guest controller.
Candidate containers receive only their published task inputs. Native separate
verification receives pristine data with network disabled and no model access.

## 1. Install inside the guest

Allow about 12 GiB RAM and 40 GiB disk for the native runtime and images.
Install Docker Engine and its Compose plugin inside the guest using
[Docker's Ubuntu instructions](https://docs.docker.com/engine/install/ubuntu/).
The tested guest has Docker Engine 29.1.3 and Compose 2.40.3. Do not mix upstream
Docker packages with Ubuntu's `docker.io` packages. OS and Docker provisioning
are prerequisites, not a newly validated bootstrap procedure.

These remaining setup commands are for the guest, not the developer's host:

```sh
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 python3-venv socat nftables
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
sudo touch /etc/workpaperbench-local-profile
```

Start a new login shell so Docker group membership takes effect. The marker
declares this dedicated environment. It does not create isolation by itself.

```sh
git clone https://github.com/CaoimhConway/workpaperbench.git
cd workpaperbench
git checkout v0.5.0-local.4
python3 -m venv .venv
.venv/bin/pip install -e . harbor==0.23.0
mkdir -p .local
curl --fail --location \
  --header 'Accept: application/vnd.github.raw+json' \
  https://api.github.com/repositories/1024554267/contents/scripts/install.sh?ref=8b66a51036c1e20920a17cdd049fdf55c968d683 \
  --output .local/hermes-install.sh
printf '%s\n' '25d3c95550e5ed7c0eec180a7d78dde765721c4e33639ab257c154c0a6e7554f  .local/hermes-install.sh' | sha256sum --check
./wpb guest preflight
```

Preflight requires Docker's default bridge gateway `172.17.0.1`. The runner
checks the pinned native adapter and installed Hermes revision. Runtime setup
downloads public dependencies before candidate egress is restricted. Bootstrap
dependencies are not fully locked, so retain setup failures as infrastructure
outcomes. The validated native route uses the dedicated Ubuntu guest. Other
distributions and container engines remain unverified.

## 2. Verify the path without a model

```sh
./wpb guest grade --task c01 --artifacts examples/block-workpaper-v7 \
  --attempt external-reference-1
./wpb guest smoke --attempt external-transport-1
```

The authored reference should pass financial, evidence, robustness and delivery
checks. The smoke uses two scripted Chat Completions responses, a real Hermes
terminal call and an intentionally invalid `{}` workpaper. It should pass its
transport proof while separate verification rejects delivery. This is a harness
test with `inference: false`, not a model evaluation or financial score. Port
18080 must be free during the smoke.

Both runs retain `.raw/local-trials/<attempt>/receipt.json` and `verifier.json`.
The smoke also writes `transport-smoke.json`. Always use a new attempt ID.

## 3. Configure and run your compatible model

Serve a model with tool-capable Chat Completions at
`http://172.17.0.1:18080/v1` as seen from candidate containers. Its `/models`
response must contain the configured model ID. It must accept the harmless
`Authorization: Bearer local-only` placeholder without requiring a private key.
Bind the user-managed server to the guest bridge address, or forward an existing
server to that address. No inference proxy or provider adapter is supplied.

For an endpoint already forwarded to guest loopback port 18080, the bridge
listener is:

```sh
socat TCP-LISTEN:18080,bind=172.17.0.1,reuseaddr,fork TCP:127.0.0.1:18080
```

Keep that listener running. Do not expose unrelated host services through it.
Candidate egress allows this one bridge port and loopback. Other external
addresses, guest services and DNS are blocked after setup.

Copy [the minimal profile](../config/external-model.example.json), then set the
model ID, immutable weights revision and serving runtime name/version:

```sh
cp config/external-model.example.json .local/my-model.json
```

The example declares 65,536 context tokens, 24 native tool-loop turns,
4,096 generated tokens per request and 3,600 candidate seconds. Set compatible
budgets before running. Temperature, top-p and seed are explicit. Hermes can
make a forced final request at its turn limit, so turns are not an exact API
request count. Setup has a separate 1,200-second limit and the verifier has
180 seconds. No compression or fallback model is enabled.

The endpoint's model ID and native runtime revision are checked. Model revision,
serving runtime, context and generation settings are declarations, not proof
that a user-managed server honored them. Preserve your server configuration and
request logs when making model comparisons. Use equal settings and fresh
attempts for a controlled comparison.

```sh
./wpb guest run --dataset workflow-v7 --task c01 \
  --profile .local/my-model.json --attempt my-model-c01-1
./wpb guest report --attempts my-model-c01-1 \
  --output .local/my-model-report.json
```

Development task IDs are `a01 a02 b01 b02 c01 c02`. Run one at a time, changing
`--task` and `--attempt`. The low-level runner rejects model execution on the
24 evaluation tasks during the current development phase. Their references and
controls can be verified without inference.

## Read and replay the result

A successful process exit means a receipt was produced. Read its verdict to
determine whether the workpaper passed. Reports separate query repairs,
preservations, regressions and remaining defects, alongside numerical, claim,
evidence, robustness and delivery checks. Candidate timeout/partial exit remains
visible. Infrastructure or isolation failure is not a reasoning score.

Exact submitted JSON is retained as `raw-answer.json`, normalized JSON as
`answer.json` when parseable, and SQL under `raw-sql/`. Raw native traces remain
under the attempt directory. Screen them before sharing. Receipts bind artifact,
task, scorer and configuration hashes. Reports reject mixed scorer or model
configurations and never replace existing output files.

To score a retained submission again, copy `raw-answer.json` to `answer.json`
in a fresh artifact directory and add its exact `raw-sql/*.sql` files. Use
`guest grade --dataset <original-catalog> --task <original-task> --artifacts
<directory> --attempt <new-id>`. This creates an inference-free replay, not a
new evaluation. Preserve the original receipt and catalog identity when
comparing corrections. Historical results do not measure discrimination on
the current catalog.

Use `./wpb` for the current interface. The installed `workpaperbench` console
command preserves the historical release interface. The owner-specific measured
model profiles remain in [LOCAL.md](LOCAL.md).
