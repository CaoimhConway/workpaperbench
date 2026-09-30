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

## Verify a workpaper without inference

The project environment and guest setup above are sufficient for grading. No
weights, model server or Hermes installer are required for this path.

```sh
./wpb grade --dataset workflow-v5 --task c01 \
  --artifacts examples/block-workpaper --attempt block-example-1
```

The checked-in example is an authored reference. The expected checks are
`financial_answer=true`, `evidence=true`, `robustness=true` and `delivery=true`.
The receipt is retained under `.raw/local-trials/block-example-1/receipt.json`.
Use a fresh attempt ID for another verification. Failed financial checks produce
a receipt too, so inspect the verdict rather than treating process exit as a score.

The `./wpb` grading wrapper transfers only the required inputs to the isolated
guest. Its model preflight is specific to the measured Intel Mac Pro, but neither
the task format nor the financial verifier requires that processor. The underlying
Linux entry point is `scripts/local_trial.py`, which is also used by the wrapper.
It requires a dedicated guest marked by the checked-in provisioning profile,
Docker and native Harbor. A general-purpose host is not an equivalent environment.
Other guest/platform combinations have not been validated here.

## Run the measured local model

The measured default is Qwen3.5-9B **Q4_K_M** from
[the pinned quantization repository](https://huggingface.co/twoody/Qwen3.5-9B-GGUF/tree/b647a5938c8cf40d1c3553ddd9bf2892895f0110).
Place `Qwen3.5-9B-Q4_K_M.gguf` in `.local/models/`. The publisher declares Apache
2.0 and official base revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
Conversion is not independently reproduced. Keep the license and download provenance.

The tested CPU server is [llama.cpp b11516](https://github.com/ggml-org/llama.cpp/releases/tag/b11516),
commit `d4d82d67f`. Extract the official `llama-b11516-bin-macos-x64.tar.gz` asset
under `.local/runtime/`, producing `.local/runtime/llama-b11516/llama-server`.
Its archive SHA256 is `e0b7a1c44132b6b44e349a4fa9813ee2e67bd26de1325c91bfecec37daf01000`.
The [profile](../config/local/qwen35-9b-terminal-24.json) verifies weights, binary and
embedded tool/chat template before launch. Weights, binaries and raw logs remain
private local assets excluded from Git.

This configuration uses eight CPU threads, one request at a time, 65,536 tokens
of native context, thinking mode and no context shifting. Each candidate has
24 turns, 4,096 generated tokens per turn and 3,600 seconds of candidate
wall time. This is the native tool-loop budget. Hermes may issue a forced final
request at the limit, and capped partial sessions remain failures. Actual request
counts and elapsed wall time are retained per trial. Native terminal tools receive
generic filesystem-delivery guidance.
Its native three-file development smoke delivered all artifacts in 15m26s and
reached fresh verification. Evidence and delivery pass. A claim about the starting
query and duplicate-export preservation fail, as shown in
[the compatibility proof](../reports/local/setup-terminal-budget-validation.json).
Financial outcomes are excluded from setup selection. The earlier eighteen-turn
profile and its paused scored schedule remain separately preserved.
[Schedule 4](../config/local/development-schedule-4.json) pins three fresh prototype
attempts under the selected configuration, declared before any scored call.
All three slots are now retained. Brale reached verification, while Block ended
with a native partial exit and Microsoft timed out at 3,600 candidate seconds.
The latter two have no JSON and unassessed semantic checks. Further calibration
is paused. This is a tested local integration with limited workflow coverage,
not a guarantee that the default model completes every case.
[Actual results](../reports/local/workflow-development-budget-1.json) preserve
the failed attempts alongside the assessable workpaper.

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
./wpb run --dataset workflow-v5 --tasks a01 b01 c01 --attempt my-dev
```

Each identifier is unique. Existing attempt directories are rejected. The runner
uses fresh candidate state, and only one native trial may run at a time. A profile
selects the exact weights, template, context, generation settings and bounds.
Reports reject mixed profiles and task/scorer identities.

## Submit replay and report

Submit an engineer's JSON workpaper or workflow artifact directory:

```sh
./wpb grade --task c03 --answer /path/to/answer.json --attempt engineer-1
./wpb grade --dataset workflow-v5 --task b01 --artifacts /path/to/workpaper --attempt engineer-workflow-1
./wpb replay --task c03 --retained my-block-1 --attempt replay-block-1
./wpb report --attempts my-block-1 --output reports/local/my-block-report.json
```

Replay uses exact retained JSON and SQL bytes in a new inference-free native
verification. `--retained all` selects current-catalog retained workpapers.
`replay --legacy --retained final-c03-inexpensive-1 --attempt old-block-review`
uses the original published candidate dossier with corrected challenge-1.1.3
scoring. It does not pretend the old answer used repaired Microsoft headings.
Use `--retained all` with `--legacy` to replay all available historical slots.

For a workflow replay and report, keep the catalog and task explicit:

```sh
./wpb replay --dataset workflow-v5 --task c01 \
  --retained block-example-1 --attempt block-example-replay-1
./wpb report --attempts block-example-1 block-example-replay-1 \
  --output reports/local/my-workpaper-review.json
```

Reports compare original artifact hashes and refuse to mix scorer versions or
model configurations. Output files are created exclusively, preserving earlier reports.

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
