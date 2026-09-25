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

The measured default is Qwen3-4B-Instruct-2507 **Q4_K_M** from
[the pinned quantization repository](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/tree/a06e946bb6b655725eafa393f4a9745d460374c9).
Place `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` in `.local/models/`.
The quantizer declares the official Qwen base and Apache 2.0 license. Its exact
base conversion revision is not independently established. The profile pins the
actual embedded tool/chat template, which differs from the official tokenizer
configuration. Keep the license and download provenance with the weights.

The tested CPU server is [llama.cpp b11516](https://github.com/ggml-org/llama.cpp/releases/tag/b11516),
commit `d4d82d67f`. Extract the official `llama-b11516-bin-macos-x64.tar.gz` asset
under `.local/runtime/`, producing `.local/runtime/llama-b11516/llama-server`.
Its archive SHA256 is `e0b7a1c44132b6b44e349a4fa9813ee2e67bd26de1325c91bfecec37daf01000`.
The selected [profile](../config/local/qwen3-4b-instruct-2507-delivery.json) verifies
weights, binary and actual template before launch. Weights, binaries and raw logs
remain private local assets excluded from Git.

This profile uses eight CPU threads, one request at a time, 65,536 tokens of
native context without YaRN, non-thinking generation and no context shifting.
Each candidate has twelve turns, at most 4,096 generated tokens per turn and
1,800 seconds of execution wall time. Native file and terminal tools receive
only generic filesystem-delivery guidance. The successful compatibility smoke
wrote a schema-valid workpaper but failed financial, evidence and preservation
checks. That is a selected runnable setup, not a quality or frontier claim.
The [declared scored schedule](../config/local/development-schedule.json) is separate.

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
