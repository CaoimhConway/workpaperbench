# WorkpaperBench - Reproducible evaluations for financial research agents.

Can an agent calculate the right number - and support the conclusion?

Eight small native Harbor tasks test financial evidence selection, metric
comparability and replayable SQL using Hermes Agent with one hosted model. Software is complete and the full native gate passed 64
controls. The frozen 48-slot evaluation is running. Development exploration is recorded separately.

This authored workpaper derives Tesla calendar Q1 2024 R&D from
[its Q2 filing](https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm).
The three-month R&D amount is 1,074 USD million and the six-month amount is 2,225.
Q1 is **1,151 USD million**. Q2 sequential change is **-6.689834926%**. The denominator
is Q1 and both operands use 2024 columns. This demonstration is an authored
reference, separate from saved submissions.

```sql
WITH periods AS (
  SELECT MAX(CASE WHEN period='Q2' THEN amount_million END) AS q2,
         MAX(CASE WHEN period='H1' THEN amount_million END) AS h1
  FROM expenses
  WHERE entity='Tesla' AND year=2024 AND metric='R&D'
)
SELECT h1-q2 AS value FROM periods
```

Inspect it without a key or container:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/workpaperbench demo
.venv/bin/python -m pytest -q
```

Development tasks are wp01/wp02/wp05. Evaluation tasks are wp03/wp04/wp06/wp07/wp08.
The two filing tasks preserve concise source facts. Other cases are original
synthetic fixtures. The fixed Ethereum USDC capture failed through the two
permitted public RPC paths, so wp04/wp08 explicitly share one synthetic corpus.
This is a materially weaker empirical case and supports no claim about observed
chain activity. [DATA_SOURCES.md](DATA_SOURCES.md) records origins, direct source
locators, redistribution and source overlap.

A uses the full common requirements and structural checker. B adds one 230-word
contract-check skill, supplied as appended instruction and the same discoverable
skill file. Development runs exposed extra output claims, prose citations and
hardcoded SQL despite correct numbers. The skill targets those contract/replay
lapses. Its one delivery check passed, without establishing causal improvement.
Both final arms receive the same corrected common requirements.

Strict completion requires every requested value, unit, evidence context,
availability decision, bounded conclusion and SQL replay. Separate diagnostics
remain visible. Changed-input fixtures reject remembered constants and selected
join errors, without proving that arbitrary SQL generalizes. The checker only
validates structure. The separate native verifier replays constrained SQL against
pristine original and declared synthetic changed inputs. Candidate code and
candidate databases are never executed by the host.

All container tests and live slots run on standard GitHub-hosted Ubuntu 24.04 VMs.
Each live slot gets fresh containers and a 600-second solve allowance separate
from 1200-second cold setup. Native file/terminal/skills toolsets are enabled,
memory and delegation are disabled, and the turn cap is 90. The model is
`qwen/qwen3.6-35b-a3b` on OpenRouter's default route, which may vary providers.
[config/runtime.json](config/runtime.json) records pins and effective settings.
The timestamped Hermes revision is checked before solving. Upstream bootstrap and
dependency downloads remain moving parts. The three genuine installed-adapter
compatibility fixes are described in [build-notes/NATIVE_COMPATIBILITY.md](build-notes/NATIVE_COMPATIBILITY.md).

The candidate environment receives the dedicated lifetime-capped inference key.
Its terminal can read that key. Native TCP filtering allows the inference host,
but DNS/ICMP remain residual channels. This is not absolute egress isolation or
keyless execution. The separate verifier uses a network-none namespace and has
no inference key or Docker socket. Candidate inputs exclude gold, project checkout and
Git history, GitHub credentials and host sockets. No paid key is provided to
push or pull-request CI.

Remote native controls use this tested command:

```sh
gh workflow run ci.yml --repo CaoimhConway/workpaperbench --ref main -f integration=true -f scope=full -f capture=false -f setup=false
```

The completed development dispatch used:

```sh
gh workflow run benchmark.yml --repo CaoimhConway/workpaperbench --ref main -f mode=pilot -f batch=treatment -f manifest_id=development-v1
```

It resumes only genuinely unstarted slots. All 12 development slots are already
attempted, so redispatch does not provide new score-based retries. Native transport
retries remain within each slot and their individual counts are not reported.
Run IDs, evidence, resource accounting and gate state are in
[BUILD_STATUS.md](BUILD_STATUS.md). Evaluation-not-tuned cases have no model
exposure before freeze. The final fixed campaign has 30 evaluation and 18
separate development slots, with three fresh attempts per task/arm. There is no
best-of-three or independence/significance claim. Scope-only evidence-limit
questions can partly cue the answer and are not open-world discovery tests.

To replace a task inside this eight-task pack, edit its original source JSON,
review sources and direct calculations, then run `python scripts/build_tasks.py`.
The generated task includes candidate inputs and separate trusted tests. Add
valid alternatives and plausible wrong controls, run local tests and the native
Actions gate, and create a new freeze before new scored exposure. Do not modify
the released freeze or selectively retune an exposed comparison.
