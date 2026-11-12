# Workflow methods

The default catalog is `workflow-v15-canonical-400f60b5b3b6` (construction
track), scored by `workflow-1.2.1`. It has six development and 24 evaluation
tasks, all available for external model runs. Each task requests three SQL
result tables and three claim verdicts, delivered as `answer.json` and three
named `.sql` files. The [Block example](../examples/block-workpaper-v15) is an
authored reference. The [validation record](../reports/workflow-v15/README.md)
lists the software checks for this catalog.

## Scorer files

Current workflow catalogs embed `workflow-1.2.1` from the frozen scorer below
as `tests/workpaperbench/workflow_grading.py` in each task.
`workpaperbench/workflow_grading.py` is the frozen `workflow-1.0.0` scorer kept
for historical catalogs. Its path does not identify the current implementation.

| File | Version | Catalogs or retained review bindings |
| --- | --- | --- |
| [config/scorers/workflow-1.2.1.py](../config/scorers/workflow-1.2.1.py) | `workflow-1.2.1` | `workflow-v10` through `workflow-v15`, `workflow-hard-pilot-v1`, `workflow-hard-pilot-v2`, `workflow-hard-eval-v1` |
| [config/scorers/workflow_sql_worker-1.2.1.py](../config/scorers/workflow_sql_worker-1.2.1.py) | 1.2.1 worker snapshot | `workflow-v10` through `workflow-v15`, `workflow-hard-pilot-v1`, `workflow-hard-pilot-v2` |
| [config/scorers/workflow_hard_sql_worker-1.0.1.py](../config/scorers/workflow_hard_sql_worker-1.0.1.py) | `workflow-hard-sql-1.0.1` | `workflow-hard-eval-v1` |
| [workpaperbench/workflow_grading.py](../workpaperbench/workflow_grading.py) | `workflow-1.0.0` | `workflow-v1` through `workflow-v4` |
| [config/scorers/workflow-1.1.0.py](../config/scorers/workflow-1.1.0.py) | `workflow-1.1.0` | `workflow-v5` |
| [config/scorers/workflow-1.2.0.py](../config/scorers/workflow-1.2.0.py) | `workflow-1.2.0` | `workflow-v6` through `workflow-v9` |
| [workpaperbench/workflow_sql_worker.py](../workpaperbench/workflow_sql_worker.py) | Unversioned worker | `workflow-v1` through `workflow-v9` |
| [workpaperbench/challenge_grading.py](../workpaperbench/challenge_grading.py) | `challenge-1.0.0` | `challenge-v1` development |
| [config/scorers/challenge-1.1.0.py](../config/scorers/challenge-1.1.0.py) | `challenge-1.1.0` | Original `challenge-v1` evaluation |
| [config/scorers/challenge-1.1.1.py](../config/scorers/challenge-1.1.1.py) | `challenge-1.1.1` | Retained `challenge-v1` review `5141a5569da6` |
| [config/scorers/challenge-1.1.2.py](../config/scorers/challenge-1.1.2.py) | `challenge-1.1.2` | Retained `challenge-v1` review `e8bab96d4e9c` |
| [config/scorers/challenge-1.1.3.py](../config/scorers/challenge-1.1.3.py) | `challenge-1.1.3` | `challenge-v2` and the current `challenge-v1` scoring review |
| [workpaperbench/challenge_sql_worker.py](../workpaperbench/challenge_sql_worker.py) | Unversioned worker | `challenge-v1`, `challenge-v2` and shared SQL helpers for workflow workers |
| [workpaperbench/grading.py](../workpaperbench/grading.py) | `1.2.0` | `real-v1` and reviewed legacy `wpb-v1` |
| [workpaperbench/sql_worker.py](../workpaperbench/sql_worker.py) | Unversioned worker | `real-v1` and reviewed legacy `wpb-v1` |
| [config/scorers/workflow_hard_sql_worker-1.0.0.py](../config/scorers/workflow_hard_sql_worker-1.0.0.py) | 1.0.0 worker snapshot | No retained catalog selects this file |

These selections follow the manifests and [catalog loader](../workpaperbench/catalog.py).
Historical Challenge bindings are in its [development](../datasets/challenge-v1/manifests/development.json)
and [evaluation](../datasets/challenge-v1/manifests/evaluation.json) manifests,
[retained reviews](../config/scoring-reviews/) and [current review](../datasets/challenge-v1/scoring-review.json).
The [legacy review](../config/review.json) binds the reviewed `wpb-v1` implementation.
Workers without a version field are identified by SHA-256. Later manifests can
retain older implementation hashes as provenance alongside their selected scorer
and worker paths.

## Construction and maintenance

| Condition | Construction, workflow-v15 | Maintenance, workflow-v7 |
| --- | --- | --- |
| Candidate receives | Dossier, normalized observations and output contract | Same financial inputs plus three starting queries |
| Starting SQL | None | 61/90 queries already correct across the catalog |
| Required work | Construct all three queries and assess the claims | Check existing work, repair defects and preserve correct results |
| Report | Original and control-inclusive correctness | Correctness plus repair, preservation, regression and unrepaired transitions |
| Interpretation | Bounded workpaper construction | Supplied-work maintenance with a predictable defect-count prior |

Construction removes all 90 starting queries, so there is no defect count to
infer and no correct SQL to copy. Source values, reference SQL, numerical
targets, controls, scorer and source-group splits match the maintenance track.
The [builder](../scripts/build_workflow_construction.py) rewrites the
instructions and two Brale claims that referred to the removed SQL. The new
claims compare June and May signature lag (16 versus 12 days, supported) and
assert that at least one observation has reserves greater than circulation
(contradicted by both dated equalities). [Tests](../tests/test_workflow_construction.py)
calculate these relationships independently.

Catalog and task identities keep the tracks apart. Reports reject mixed
catalogs and never transfer maintenance baselines to construction.

## Measurement contract

- **Numerical.** Every requested row must match on declared keys and column
  names, within explicit absolute tolerances. Row and column order are ignored.
  Declared source-label aliases map to the same category before matching.
  Duplicate keys fail. Keys and aliases are public in each `output_contract.json`.
- **Claims.** Supported means the supplied evidence entails the assertion,
  contradicted means it entails the negation, and unresolved means neither
  follows. Claims concern the original dossier only. A claim that a complete
  supplied table reports a disclosure it omits is contradicted. A claim about
  an unobserved economic value can be unresolved.
- **Evidence.** Each table and claim must cite at least one reviewed sufficient
  set of source IDs. Relevant extra context and alternative sufficient paths are
  accepted. Every `namespace:s<digits>` token is checked, including unknown or
  unrelated IDs. Prose without IDs supplies no evidence. This tests source
  selection, not the truth of explanations. A rejected valid path is a grader
  defect.
- **Robustness.** The same SQL must stay correct on every synthetic control.
  Three to six controls per task test specific dependencies, not all possible
  inputs. Different SQL passes when its results agree.
- **Delivery.** Exactly the requested files, bounded sizes, unique IDs and safe
  relative basenames. A structural rejection prevents SQL replay and leaves the
  other dimensions unassessed rather than failed.

In maintenance, preservation means an initially correct query stays correct on
original inputs and controls. Repair, regression and unrepaired cover the other
before and after combinations.

Reports show each dimension separately, with per-table execution, column, row,
key, text or numeric mismatch reasons. `financial_answer` combines numbers and
claims for continuity. Completion requires every substantive check and delivery.

## Validity revisions and continuity

Each revision has its own catalog identity. Earlier catalogs, saved submissions
and results keep theirs, and corrections never rescore old answers as answers
to a new version.

| Version | Change | Record |
| --- | --- | --- |
| v5 | Fixes blanket-citation acceptance and zero-residual shortcuts. 51 independent residual columns meet synthetic discrepancies, and three algebraic identity residuals are removed. | - |
| v5 correction | Scorer 1.2.0 accepts published filing-label aliases and both `contradicted` and `unresolved` for ambiguous historical assertions. Targets, tolerances, SQL restrictions and controls are unchanged. | [Builder](../scripts/review_workflow.py), [corrected replay](../reports/workflow-v5/corrected-replay.json) |
| v6 | Replaces 30 ambiguous assertions with source-grounded claims: ten supported, ten contradicted and ten unresolved. The 90 claims are 37 supported, 43 contradicted and 10 unresolved. No held-out candidate outcomes informed these changes. | [Claim review](../config/workflow-claim-review.json) |
| v7 | Accepts Microsoft's segment table alone as sufficient evidence for three outputs. | [Builder](../scripts/build_workflow_evidence_alternative.py) |
| v8 | Accepts all nine cross-report Brale citation pairs for the lag table and its claim. Validation adds 147 reference and control expectations and native network fixtures. | [Validation](../reports/workflow-v8/validation.json) |
| v9 | Accepts the January and February PYUSD summaries for asset coverage and defines Treasury valuation residuals. | [Native validation](../reports/workflow-v9/direct-harbor-validation.json) |
| v10 | Removes Block's numerical singleton key, specifies Uber's EBITDA and residual directions and PYUSD's reported stocks, and accepts Uber's segment comparison alone for its commission claim. Scorer `workflow-1.2.1` accepts the full escaped JSON envelope. | [Builder](../scripts/build_workflow_contract_revision.py) |
| v11 | Adds independent operands to block shortcuts: c01 subscription costs, b06 consumer activity, b03 consumer spot volume and c04 operating expenses on both bases. | [Dependency audit](../reports/workflow-v11/dependency-audit.md), [release record](../reports/workflow-v11/README.md) |
| v12-v14 | Evidence and measurement contract corrections. | - |
| v15 | Clarifies financial bases, accepts sufficient evidence alternatives and corrects the reported baseline in one authored forecast. | [Validation](../reports/workflow-v15/README.md) |

## Validity assessment

- **Starting SQL.** In isolated verification, 61/90 maintenance starting
  queries pass original inputs and every control, and each is byte-identical to
  the reference SQL. Twenty-nine tasks have exactly one faulty query and `b04`
  has none. That repeated defect count is a shortcut prior, so maintenance
  measures bounded repair, not open defect discovery. Construction removes the
  starting queries.
- **Claim baselines.** Constant answers score 43/90 (`contradicted`), 37/90
  (`supported`) and 10/90 (`unresolved`) before evidence or whole-task checks.
  Grading supports bounded uncertainty about an assertion. It does not measure
  confidence calibration or free-text entailment.
- **Supplied assistance.** Both tracks supply normalized observations,
  excerpts, definitions, units and formulas, which removes most source
  extraction and search by design. Difficulty comes from period reconstruction,
  unit conversion, economic denominators, signed changes and identifiability.
- **Recomputed transitions.** The nine retained workflow-v5 query transitions
  give three repairs, five preservations and one regression on original inputs.
  Including controls gives two repairs, five preservations, one regression and
  one unrepaired defect, Brale's duplicate export. Block's apparent category
  failures were grader errors.

Maintenance reports use the [identity-bound starting receipts](../reports/workflow-v7/starting-sql.json).
A numerical or claim failure is an observed outcome, not proof of its internal
cause. Missing deliveries and infrastructure failures leave semantic checks
unassessed.

## Reproduce the quality checks

These checks need no model or inference server. Install the
[portable Linux/Docker harness](RUNNING.md), then run:

```sh
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q
.venv/bin/python scripts/build_workflow_contract_adjudication.py --check
.venv/bin/python scripts/validate_workflow_quality.py \
  --dataset workflow-v15 --native-prefix my-validity \
  --output .local/my-validity-prototypes.json
.venv/bin/python scripts/validate_workflow_quality.py \
  --dataset workflow-v15 --tasks all --output .local/my-validity-suite.json
```

Use fresh output paths and attempt prefixes. The prototype command runs
Microsoft, Brale and Block through native Harbor and the same separate
verifier. The sweep checks authored references, reordered equivalent SQL with
source aliases and explanatory citations, citation dumping, constant-zero
residuals and an always-unresolved claim baseline. These are engineering
controls, not model trials. The `--executor local-lima` option keeps the
historical Mac/Lima wrapper and is not the default.

Standalone sweep and replay containers use no network, a read-only root,
bounded temporary storage and dropped capabilities. Native verifier receipts
check for no network, no inference credential and no Docker socket. SQL workers
enforce read-only authorization, a 256 MiB address space, two-second CPU and
1.5-second progress limits and bounded output. See the
[resource and boundary proof](../reports/local/local-boundary-validation.json).
These probes are not a security proof for arbitrary workloads.

## Evaluation limits

- The 24 evaluation tasks come from distinct source-window groups with no
  development overlap. Held out means not used for candidate-model tuning here,
  not private or absent from training data. Public sources, related issuer
  templates and published references create contamination and shortcut risks.
- Observed facts, normalized observations, authored defects, synthetic
  controls, references and model submissions have different provenance.
  Publication, signature, economic-period and retrieval dates are distinct. The
  [source audit](../reports/local/workflow-source-review.json) retains
  derivations.
- A measured comparison needs frozen profiles and budgets, every failure
  retained, paired per-task reporting and uncertainty across repeated attempts.
  Use the [comparison recipe](COMPARISON.md). The
  [historical comparison proposal](../config/future-comparison.json) was not
  executed. The corrected development replays shown by the demo use unequal
  settings and are not construction results.
- Independent financial-domain review and external replication are pending.
