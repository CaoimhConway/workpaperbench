# Local execution

This profile uses the Intel Mac Pro as the inference host. Docker runs only in a
dedicated Ubuntu guest. The tested guest has six CPUs, 12 GiB RAM and a 40 GiB
virtual disk. It mounts no host folders or owner credentials. Existing guests
are outside this profile.

Install the project environment with Python 3.12 and the existing package pins:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
```

The tested Lima version is 2.2.0. Its executable is expected at
`~/.local/opt/lima-2.2.0/bin/limactl`. Create the named guest from the checked-in
profile, then install native Harbor and its verifier dependency inside it:

```sh
~/.local/opt/lima-2.2.0/bin/limactl start --name=workpaperbench-local config/local-lima.yaml
~/.local/opt/lima-2.2.0/bin/limactl shell workpaperbench-local bash -lc 'python3 -m venv ~/runtime && ~/runtime/bin/pip install harbor==0.23.0 jsonschema==4.26.0'
```

The local profile uses the official Qwen3-30B-A3B GGUF Q4_K_M, revision
`e4d4bafdfb96a411a163846265362aceb0b9c63a`. Download it from the official repository
into `.local/models/Qwen3-30B-A3B-Q4_K_M.gguf`. The tested CPU server is llama.cpp
b11516, commit `d4d82d67f`, in `.local/runtime/llama-b11516/llama-server`.
The profile verifies both files against their recorded SHA256 hashes before
launch. Weights, runtime binaries and raw logs are private local assets, excluded
from Git. Keep the model's Apache 2.0 license with the download.

Retain the pinned Hermes installer from commit
`8b66a51036c1e20920a17cdd049fdf55c968d683` at
`.local/runtime/hermes-agent/scripts/install.sh`. The runner verifies the original Harbor Hermes adapter from the guest's
installed Harbor 0.23.0 distribution before retaining it in its private builder
directory and applying narrow local routing and CLI compatibility changes. It
restores the original module after every trial. The receipt hashes the effective
adapter, installer and disposable task image inputs.

The `./wpb` launcher uses the project environment and current scoring contract.
The equivalent Python entry point is `python -m workpaperbench.current_cli`:


```sh
./wpb preflight
./wpb controls --attempt boundaries-1
./wpb serve
```

Leave the server command running. In another terminal, run a single selected
published regression task, or the selected development prototypes:

```sh
./wpb run --task c03 --attempt my-block-1
./wpb run --dataset workflow-v1 --tasks a01 b01 c01 --attempt my-dev
```

Each identifier is unique. Existing attempt directories are rejected. The runner
uses fresh candidate state, and only one native trial may run at a time. A profile
selects the exact weights, template, context, generation settings and bounds.
Reports reject mixed profiles and task/scorer identities.

Submit an engineer's JSON workpaper or workflow artifact directory:

```sh
./wpb grade --task c03 --answer /path/to/answer.json --attempt engineer-1
./wpb grade --dataset workflow-v1 --task b01 --artifacts /path/to/workpaper --attempt engineer-workflow-1
./wpb replay --task c03 --retained my-block-1 --attempt replay-block-1
./wpb report --attempts my-block-1 --output reports/local/my-block-report.json
```

Replay uses exact retained JSON and SQL bytes in a new inference-free native
verification. `--retained all` selects current-catalog retained workpapers.
`replay --legacy --retained final-c03-inexpensive-1 --attempt old-block-review`
uses the original published candidate dossier with corrected challenge-1.1.3
scoring. It does not pretend the old answer used repaired Microsoft headings.
Use `--retained all` with `--legacy` to replay all available historical slots.

The original installed console command and `python -m workpaperbench.cli` remain
frozen historical interfaces. Current usage enters through `current_cli`.
Original freeze files and historical review receipts are not updated to bless
new runtime changes.

Candidate setup downloads public dependencies before execution is locked to
local transport. Native separate verification has network-none, no inference key,
no Docker socket and pristine task data. Only bounded authorized SQL is replayed.
Format rejection never executes SQL. Raw traces stay private until screened.

The current publication audit is `.venv/bin/python scripts/audit_current.py`. It
checks retained historical task, source and executable hashes.
