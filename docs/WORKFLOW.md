# Workflow methods

The current catalog is `workflow-v7-canonical-fca4003d0a15`, using scorer
`workflow-1.2.0`. Six development and 24 evaluation cases each request three SQL
result tables and three claim verdicts. Deliver `answer.json` and three named
`.sql` files. The [Block example](../examples/block-workpaper-v7) is an authored
reference, not a model submission.

## Measurement contract

Numerical correctness requires every requested original row, matched by declared
keys and column names with explicit absolute tolerances. Row and column order do
not matter. Declared source-label aliases map to the same economic category
before key matching. Normalized duplicate keys and swapped category values fail.
Text keys and aliases are public in each `output_contract.json`.

Claim verdicts are a separate diagnostic. Supported means the supplied evidence
entails the assertion, contradicted means it entails the negation, and unresolved
means neither follows. Claims concern the original dossier only. A false claim
that a complete supplied table reports a particular disclosure is contradicted.
A claim about an unobserved economic value can instead be unresolved.

Evidence is checked separately for each table and claim. At least one reviewed
support set must be present. Relevant extra context and alternative sufficient
paths are accepted. Source IDs use `namespace:s<digits>` locators and may be
embedded in explanations. Every source-shaped token is checked, including unknown
or unrelated IDs. Explanation-only prose contributes no evidence. This tests
source selection, not the entailment or truthfulness of arbitrary explanations.
A valid rejected evidence path remains a grader defect requiring review.

Robustness requires correct recomputation across every synthetic control.
Preservation means a query that was initially correct remains correct on the
same original inputs and controls. Repair, regression, and unrepaired outcomes
use the other three before/after combinations.
Different SQL is accepted when its observable results agree on original and
control inputs. Three to five controls test specific dependencies, not all future
inputs. Delivery requires the exact requested files, bounded sizes, unique IDs,
and safe relative basenames. Structural rejection prevents SQL replay and leaves
semantic aggregates unassessed, rather than recording failed calculations.

The report exposes numerical tables, claim verdicts, evidence, robustness, and
delivery separately. `financial_answer` combines numbers and claims for continuity.
Each table also reports execution, column, row, key, text, or numeric mismatch
reasons. Full completion requires all substantive checks and delivery.

## Validity revisions and continuity

Version 5 fixed blanket-citation acceptance and zero-residual shortcuts. Fifty-one
independent residual columns now encounter synthetic discrepancies. Three algebraic
identity residuals were removed. These controls remain unchanged in version 6.

Version 5 still rejected full Block filing labels and Microsoft citations with
explanations. Its identifiability assertions also conflated missing disclosures
with unknown economic values. The [versioned correction](../scripts/review_workflow.py)
uses scorer 1.2.0, published filing-label aliases, and explicit acceptance of both
`contradicted` and `unresolved` for those ambiguous historical assertions. All
numeric targets, tolerances, SQL restrictions, and controls remain unchanged.
The [corrected replay report](../reports/workflow-v5/corrected-replay.json) preserves
original verdicts alongside corrected diagnostics and exact retained file hashes.
It is not new inference and does not rescore old answers as version 6 answers.

Version 6 replaces each ambiguous assertion using a
[source-grounded claim review](../config/workflow-claim-review.json). Ten replacements
are supported calculations, ten are contradicted disclosure/scope assertions,
and ten are unresolved economic assertions. The complete 90-claim distribution
is 37 supported, 43 contradicted and 10 unresolved. Twenty cases have no unresolved
claim and ten have one. Opaque IDs and deterministic ordering remove the fixed
uncertainty slot. Every new assertion has one accepted verdict.

In version 6, original source observations, starting/reference SQL, financial
targets, evidence options for tables, and synthetic databases remain byte-identical
to version 5 or equal as structured targets. No held-out candidate outcomes informed these
changes. Source-based reference/control validation is distinct from candidate-model
tuning. Historical releases, task catalogs, scorers and correction receipts retain
their identities. Public label distributions still permit statistical shortcuts,
and this revision does not establish calibrated abstention or human agreement.

Version 7 corrects one sufficient-evidence omission. Microsoft's `a03:s05`
segment table includes consolidated revenue and operating-income Total rows
for both three- and six-month periods in both years. Those totals independently
reproduce `quarter_model`, `quarter_reconciliation`, and the margin-change claim.
The [versioned builder](../scripts/build_workflow_evidence_alternative.py) accepts
that table alone for those three outputs, retaining the income-statement route.
Source values, SQL, financial targets, controls, claim assertions and verdicts,
and scorer 1.2.0 are unchanged. Historical catalogs and receipts are untouched.

## Validity assessment

The starting-SQL check was rerun on all 30 current tasks in isolated verification.
**61/90 queries pass original inputs and every control.** They are also
byte-identical to the reference SQL. Twenty-nine tasks have exactly one faulty
query, while `b04` has none. Existing correct code is realistic assistance for
maintenance work and provides preservation opportunities. The repeated defect
count supplies a shortcut prior. This collection therefore measures bounded
maintenance, not unconstrained defect discovery or writing a workpaper from scratch.
No coverage gap justified adding defects or expanding the dataset.

Candidate inputs include normalized observations, source excerpts, definitions,
units, formulas, and starting SQL. These intentionally remove much of source
extraction and search. They are disclosed assistance, not hidden reference access.
Candidate images omit gold, solutions, tests, checkout history and credentials.
Published references remain a contamination risk outside that execution boundary.
Source-group separation does not make related issuer templates independent.

Claim-only constant answers achieve 43/90 for `contradicted`, 37/90 for
`supported`, and 10/90 for `unresolved`, before evidence or whole-task checks.
The current 14 ordered verdict patterns remove the old universal unresolved slot,
but these label priors remain. Grading supports bounded uncertainty about an
assertion. It does not measure confidence calibration or free-text entailment.
Financial difficulty comes from period reconstruction, unit conversion, economic
denominators, signed changes and identifiability, within the supplied contract.

The nine retained workflow-v5 query transitions were independently recomputed
using matching frozen tasks and scorers. Original inputs give three repairs,
five preservations and one regression. Including controls gives **two repairs,
five preservations, one regression and one unrepaired defect**. The latter is
Brale's duplicate-export failure. Microsoft's correct starting basis-point query
regressed. Block's apparent category failures were grader errors. Neither scorer
corrections nor improved original-input results are automatically robust repairs.

Current reports use the [identity-bound starting receipts](../reports/workflow-v7/starting-sql.json)
and expose per-query transitions on both scopes, plus initially correct and
incorrect opportunity counts. Missing or rejected deliveries leave SQL transitions
unassessed. Infrastructure failures leave semantic diagnostics unassessed. A
numerical or claim failure is an observed reasoning/calculation outcome, not proof
of its internal cause. SQL execution errors remain distinguishable in table details.
Budgets, continuation history and unscored attempts must accompany interpretation.

## Reproduce the quality checks

Install the project environment and configure the separate Ubuntu guest using
[the portable execution guide](RUNNING.md). The full catalog sweep below uses the
existing [Mac/Lima maintenance wrapper](LOCAL.md), while individual native grading
and reporting use the portable `./wpb guest` path. No model or inference server is needed.

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/build_workflow_evidence_alternative.py --check
.venv/bin/python scripts/validate_workflow_quality.py \
  --dataset workflow-v7 --native-prefix my-validity \
  --output /tmp/my-validity-prototypes.json
.venv/bin/python scripts/validate_workflow_quality.py \
  --dataset workflow-v7 --tasks all --output /tmp/my-validity-suite.json
.venv/bin/python scripts/review_workflow.py --output /tmp/my-corrected-replay.json
```

Use fresh output paths and attempt prefixes. The prototype command runs Microsoft,
Brale and Block through native Harbor, then exercises the same separate verifier.
The sweep checks authored references, equivalent reordered SQL with source aliases
and explanatory citations, citation dumping, applicable constant-zero residuals,
and an always-unresolved claim baseline. Incorrect claim labels cannot be rescued
by correct SQL or evidence. These are engineering controls, not model trials.

Every verifier container uses network-none, a read-only root, bounded temporary
storage, no capabilities, no inference credential, and no Docker socket. SQL runs
only inside the isolated Linux verifier. Workers enforce read-only authorization,
256 MiB address space, two-second CPU and 1.5-second progress limits with bounded
output. Actual network and namespace checks accompany verdicts. The unchanged
worker and runner retain the earlier [resource and candidate-boundary proof](../reports/local/local-boundary-validation.json).
These probes do not constitute a security proof for arbitrary workloads.

## Evaluation limits

The evaluation split has 24 distinct source-window groups without development
group overlap. Public sources, related issuer templates, public references, and
repeated structure create contamination and shortcut risks. Held out means not
used for candidate-model tuning here, not private or absent from training.

Observed facts, normalized observations, authored starting-query defects, synthetic
counterfactuals, references, and actual submissions have different provenance.
Publication, signature, economic-period, and retrieval dates must not be confused.
The [source audit](../reports/local/workflow-source-review.json) and claim review
retain derivations. Independent financial-domain review remains pending.

A measured comparison requires frozen profiles and budgets, all failures retained,
task-level paired reporting, and uncertainty that accounts for repeated attempts.
The [future comparison](../config/future-comparison.json) remains disabled. The
three corrected development replays use different settings and include a continued
session. They do not establish workflow-v7 accuracy or a model ranking. Human
review and external replication also remain unevidenced.
