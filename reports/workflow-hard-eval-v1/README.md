# Financial reasoning supplement verification

All four `workflow-hard-eval-v1` task packages pass their authored reference,
alternative, control and native execution checks. This report establishes
package behavior, not model performance or empirical difficulty.

The frozen manifest is `workflow-hard-eval-v1-canonical-a13e5bdb16c3`, at package
checkpoint `3fbc022233bf2b6f3c621228fcd8659d37795552`. The
[task guide](../../docs/WORKFLOW_HARD_EVALUATION.md) describes each capability
and gives executable commands. [Worked references](../../datasets/workflow-hard-eval-v1/references)
and [source snapshots](../../datasets/workflow-hard-eval-v1/sources) retain
source locators, factual extracts, assumptions, hashes and financial derivations.

| Check | Result |
| --- | --- |
| References and legitimate alternatives | 20 accepted variants |
| Targeted financial mistakes | 33 rejected variants |
| Constants, incorrect verdicts and inadequate evidence | 16 rejected variants |
| Changed-input databases | 36, including relevant invariances |
| Native reference executions | 4 passed |
| Runtime materialization records | 20 verified |
| External-interface protocol fixture | Valid submission accepted, invalid submission rejected |
| Experimental SQL compatibility and restrictions | 47 isolated probes passed |
| Full repository tests | 771 passed, 76 platform skips |

The 47 SQL execution probes require the isolated Linux verifier and were among
the macOS skips. They passed separately in the pinned verifier image using
SQLite 3.40.1. Reproducible package construction uses SQLite 3.45.1 on the Ubuntu
24.04 controller. The final evidence-path bindings also pass the five focused
package tests and the complete isolated variant sweep.

[verification.json](verification.json) records all 69 variants and four native
references. [materialization.json](materialization.json) binds the expected and
observed files. [external-interface.json](external-interface.json) records the
scripted endpoint fixture. It confirms reference assets are absent from the
candidate, while a candidate terminal can read its installed inference key.
The separate verifier has no inference key, network or Docker socket. The
fixture makes no inference calls and is not a model trial.

Financial scorer `workflow-1.2.1` and its numerical, evidence and control
semantics remain unchanged. The separately versioned experimental worker
`workflow-hard-sql-1.0.0` corrects rejection of ordinary counted CTEs and
zero-column reads. Its resource limits and restrictions remain in force.
The [retired first protocol](../../config/hard-evaluation-20261023/retirement.json)
consumed no slots or inference before this correction. Candidate-visible files,
numerical answers, controls and claim verdicts remain identical to the initial
four-task freeze. Sufficient alternative claim evidence paths were added before
evaluation inference. The replacement protocol is
[hard-evaluation-20261023-r2](../../config/hard-evaluation-20261023-r2/manifest.json).

The unchanged baseline and historical bindings are recorded in
[summary.json](summary.json). Independent human financial/source review and
actual external-user testing remain pending. Four evaluation cases support
descriptive observations, not a stable general ranking or equivalence to a
larger benchmark.
