# WorkpaperBench - Reproducible evaluations for financial research agents.

Can an agent calculate the right number - and support the conclusion?

WorkpaperBench evaluates financial evidence selection, metric comparability and replayable SQL through native Harbor tasks and Hermes Agent. The build is in progress. No live experimental result has been measured yet.

A source-backed reference workpaper derives Tesla calendar Q1 2024 R&D from [its Q2 filing](https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm). The three-month R&D figure is 1,074 USD million and the six-month figure is 2,225. Q1 is **1,151 USD million**, and Q2 sequential change is **-6.689834926%**. The period columns and units matter as much as subtraction. This reference is authored, not a live submission.

```sql
WITH periods AS (
  SELECT MAX(CASE WHEN period='Q2' THEN amount_million END) AS q2,
         MAX(CASE WHEN period='H1' THEN amount_million END) AS h1
  FROM expenses
  WHERE entity='Tesla' AND year=2024 AND metric='R&D'
)
SELECT h1-q2 AS value FROM periods
```

Inspect the workpaper without a key or container:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/workpaperbench demo
.venv/bin/python -m pytest -q
```

The eight-task ceiling includes development wp01/wp02/wp05 and evaluation wp03/wp04/wp06/wp07/wp08. Three development packages are implemented first. A migration case is explicitly synthetic. An Ethereum USDC capture will be shared by two evaluation tasks when bounded source acquisition succeeds. Origins, missing labels and shared sources are disclosed in [DATA_SOURCES.md](DATA_SOURCES.md).

Both arms use the same JSON schema and structural checker. Answered claims require finite numbers, canonical units, relevant evidence and one constrained SQL statement. A separate verifier replays queries against pristine data and a declared synthetic changed-data control. A hardcoded number or a table mention that ignores its contents fails replay. Numerical correctness, evidence, availability, conclusion and replay checks remain separate in reports.

All container integration and live trials run on standard GitHub-hosted Ubuntu 24.04 VMs. This device needs only lightweight Python, Git and GitHub CLI. The native installed Hermes environment receives the dedicated capped inference key, which terminal tools in that environment may read. The separate verifier and replay worker receive no key or network. Gold, Git history, GitHub credentials and Docker sockets are excluded from candidate inputs. Effective isolation still requires the native Actions integration gate.

The explicit pilot dispatch uses the committed development schedule:

```sh
gh workflow run ci.yml --repo CaoimhConway/workpaperbench --ref main -f integration=true -f capture=false
gh workflow run benchmark.yml --repo CaoimhConway/workpaperbench --ref main -f mode=pilot -f batch=baseline -f manifest_id=development-v1
```

Run IDs and actual gate results are recorded in [BUILD_STATUS.md](BUILD_STATUS.md). Final dispatch waits for the audited freeze, development observations and completed software gate. No inference secret is available to push or pull-request CI.
