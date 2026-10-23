# Contractual decision task verification

The two development packages in
`workflow-hard-pilot-v2-canonical-5034f88e23bf` passed reference, alternative,
control and native materialization verification on October 23, 2026. These are
deterministic engineering and financial-reference checks. No candidate-model
trial or empirical difficulty claim is attached to this dataset.

The [design report](../../docs/WORKFLOW_HARD_FOLLOWUP.md) explains the capability
hypotheses and the review of the previous six successful submissions. Worked
derivations and source mappings are available for
[Ashtead](../../datasets/workflow-hard-pilot-v2/references/a01.md) and
[Veeco](../../datasets/workflow-hard-pilot-v2/references/b01.md).

## Results

| Check | Result |
| --- | --- |
| Pinned SQLite 3.45.1 build and byte-for-byte reconstruction | Passed for both packages |
| Focused financial, source, SQL and package tests on Ubuntu controller | 14 passed |
| Full repository tests | 727 passed, 28 environment-dependent skips |
| Isolated positive submissions | 10/10 accepted |
| Isolated negative submissions | 23/23 rejected for the expected reason |
| Native Harbor reference executions | 2/2 complete |
| Native materialization-integrity records | 10/10 verified |
| Changed-input databases | Eight per task, 16 distinct controls |
| Repository source, credential and frozen-contract audit | Passed |

The focused controller run includes the new pinned-builder reconstruction,
which is among the environment-dependent checks skipped on the macOS runtime.
The complete [verification JSON](verification.json) records each isolated
variant, original/control table result, claim/evidence result and native verdict.
The [materialization projection](materialization.json) retains file hashes and
outcomes without local context paths. The [verification metadata](summary.json)
binds these records, commands and protected baseline identities.

Each task accepts its reference SQL, a materially different alternative,
sufficient alternative citations, reordered rows/columns with relevant context,
and optional ungraded notes. Ashtead's alternative uses a closed-form feasible
envelope instead of vertex enumeration. Veeco's alternative uses ordered EPS
prefixes instead of exhaustive subsets and conserves holder value between cash
and shares for settlement. Tied EPS inclusion witnesses are not exact-matched.

## Rejected analytical mistakes

| Task | Intended failures, all rejected numerically |
| --- | --- |
| Ashtead | Apply the covenant always or never, omit incremental borrowing interest, add suppressed availability to commitment, deduct letters of credit twice, declare every limit attainable, or let equity override coverage. |
| Veeco | Use carrying amount as face, pay all principal in cash despite physical settlement, include full shares for mandatory-cash principal, use maturity conversion choice as EPS eligibility, add back 2029 interest, include every note, test each note against initial EPS alone, or ignore earlier dilutive issues in earnings thresholds. |

The other eight negative cases are constant original answers, wrong claim
verdicts, missing supporting evidence and unknown evidence IDs, once per task.
Constant answers pass original numerical comparisons and fail changed-input
robustness. Financial mutations fail numerical checks with correct claim and
evidence submissions, rather than failing because of malformed SQL or delivery.

## Economic checks and preserved scope

Ashtead's independently solved cash and covenant half-spaces establish limits
of USD 889.72m unattained, USD 1,036m attained and USD 1,127.08m attained.
The source supports the conditional test. Authored assumptions determine the
planning cash flows, interest and non-ABL principal repayments. A separate
financial/source review resolved the principal-repayment ambiguity before
freeze. The USD 217m difference in the disclosed headroom observations remains
unexplained.

Veeco's contractual holder-value checks and exact-rational EPS subsets agree
with the oracle. Independent checks of the EPS lower envelope and a price-root
search confirm portfolio earnings boundaries of USD 34.233282901763m and
USD 55.973898679236m, and USD 39.910790360236/share for five million gross
shares. Controls include dilution-order reversal, an exact neutrality tie and
a larger cash-principal tranche. Related synthetic addback and rate observations
are kept consistent.

Both tasks use the unchanged frozen `workflow-1.2.1` scorer, not the legacy
root grader. Claims are judged against the original dossier. SQL is rerun
against controls. Optional explanatory prose is not semantically verified.
The native references used Harbor 0.23.0 in the existing dedicated Linux guest.
Separate verifiers confirmed blocked network, no inference key and no Docker
socket. Candidate contexts contain only the canonical dossier and output
contract. Reference answers, controls, gold and verifier assets are outside the
candidate context.

All 30 workflow-v15 tasks and all three pilot-v1 tasks still match their frozen
catalog hashes. Their publication bindings, scorers, historical calibration
results and campaign configurations are unchanged. Runtime edits only register
the new dataset with the existing catalog and integrity path.

Independent human financial/source review and external-user validation remain
pending. Original indenture HTML bytes were unavailable, so those documents
have precise primary locators and extract hashes but no claimed original-file
hashes. Full captured PDFs remain local. The new cases have not been calibrated,
and their published references preclude a contamination-free claim. No model
calls, API charges, funding changes, push or publication occurred in this work.
