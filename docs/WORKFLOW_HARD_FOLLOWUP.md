# Contractual decision development tasks

`workflow-hard-pilot-v2` adds two development cases, starting from checkout
`2a4455935a7bfd5fb9d46b7f3ecdbb2d3a3d9688`. It preserves the first three pilot
tasks, their six calibration submissions and the 30-task workflow-v15 baseline.
These are further difficulty hypotheses, not a held-out suite or demonstrated
harder tasks.

## Why these two cases

The [six-observation calibration](../reports/hard-calibration-20261023/README.md)
reached the ceiling for both tested configurations. Reviewing the actual SQL
shows that Ahold's comparison basis and Microsoft's bridge conventions were
substantially specified by their contracts. Apple required real optimization,
with vertex enumeration and ordered allocation both succeeding, but its
uncertainty set and objectives were already supplied. Those tasks retain useful
financial and recomputation coverage. Six successes do not establish how either
configuration will perform on other financial decisions.

The follow-up tests whether a solver can construct the applicable financial
model from contractual and accounting definitions before calculating a result.
Task selection does not target a particular model or a desired failure rate.
Two distinct cases investigate these hypotheses without filling a larger suite
before calibration and source review.

| Task | Added capability | Closest existing coverage |
| --- | --- | --- |
| [a01, Ashtead](../datasets/workflow-hard-pilot-v2/tasks/a01/instruction.md) | Combine cash funding, incremental interest, committed borrowing capacity and a covenant that applies only after availability falls. Optimize a distribution and its equity support across regimes, including whether the sharp limit can be reached. | v15 c10 calculates numerical forecast ranges. Pilot-v1 c01 optimizes over a supplied allocation model. Neither constructs a cash-funding decision with a conditional contractual test. |
| [b01, Veeco](../datasets/workflow-hard-pilot-v2/tasks/b01/instruction.md) | Distinguish contractual cash/share settlement from potential-share accounting, construct diluted EPS after sequential antidilution decisions, and reverse-solve portfolio earnings and issuance thresholds. | v15 b09 and c08 reconcile EPS using supplied share bases. Here the denominator and numerator treatment depend on instrument terms and other dilutive issues. |

## Financial and evidence design

The [Ashtead reference](../datasets/workflow-hard-pilot-v2/references/a01.md)
maps the loan observations and covenant to the annual report. Planning cash
flows, incremental rate and timing are explicit assumptions. Reported
covenant-purpose availability remains separate from commitment less utilisation.
The source does not explain their difference. Scheduled principal is explicitly
outside the ABL, so it cannot restore revolver capacity. Suppressed availability
is not treated as a new lender commitment.

The [Veeco reference](../datasets/workflow-hard-pilot-v2/references/b01.md)
maps face principal, carrying amounts, interest, share bases and settlement
terms to the 10-K and executed indentures. A primary accounting definition
supplies dilution sequencing. The contractual 2029 conversion rate and the
slightly different 10-K observation are both retained, with priority explicit.
Hedge quantities were not sufficiently established for a net capped-call
calculation, so the requested scope is gross note issuance. Maturity scenarios
and full-period EPS sensitivities are separate hypothetical exercises.

Each dossier supplies relevant facts, definitions and necessary assumptions
without reference formulas or numerical answers. Scenarios cover different
financial regimes. Their values are authored assumptions, not fabricated issuer
observations. Full source PDFs remain outside redistributed packages. Extract
hashes, captured PDF hashes where available, locators, dates and units are
retained in the [source snapshots](../datasets/workflow-hard-pilot-v2/sources).

## Execution and grading

The existing `answer.json` plus three SQL files interface and frozen
`workflow-1.2.1` scorer are reused without extension. Registration is explicit in
the catalog and existing materialization-integrity path. Task resources match
the baseline. Qualified calibration budgets remain 3,600 candidate seconds,
with 24 Terminus-2 turns for GLM. The native Codex condition has no supported
equivalent turn limit, which remains a comparison limitation.

The scorer recomputes numerical tables on original and synthetic control
databases. Claim verdicts concern the original dossier only. Arbitrary funding
witnesses and tied EPS inclusion choices are not exact-matched. Numerical
limits, attainment flags and unique EPS values are scored. Optional explanation
and proof prose is not semantically verified.

Each package contains reference and materially different alternative SQL.
Ashtead's independent check intersects exact-rational financial inequalities.
Veeco's checks compare incremental-EPS sequencing with exhaustive subsets and
check the reverse thresholds. Controls exercise dependencies, regime changes,
ties, monetary scaling and row order. The [verification record](../reports/workflow-hard-pilot-v2/README.md)
identifies accepted alternatives and rejected financial mistakes.

On the supported Ubuntu 24.04 controller with the documented native runtime:

```sh
python scripts/build_workflow_hard_followup.py --check
python -m pytest -q tests/test_workflow_hard_followup.py tests/test_hard_convertibles.py
python scripts/validate_workflow_hard_followup.py \
  --output .local/followup-verification.json --native-prefix followup-verification
```

Use unused report and attempt identities. The validator makes no inference
requests. It uses the existing networkless isolated verifier and native Harbor
materialization for authored reference workpapers.

## Unexecuted calibration recipe

A future calibration can freeze one fresh attempt per new task for each of the
two previously qualified conditions: GLM-5.3 through OpenRouter/Terminus-2 and
GPT-6.1 Sol through native Codex. Start from the retained
[GLM condition](../config/hard-calibration-20261023/glm.json) and
[Sol condition](../config/hard-calibration-20261023/sol.json), create new experiment
and slot identities, and bind this dataset's exact manifest and task hashes.
Do not amend the earlier six-slot manifest or interpret these cases as held out.

Before execution, recheck availability of the requested model revisions and
qualified provider routes. Any changed provider, runtime or parameter mapping
requires an explicit new configuration freeze. Keep qualified wall budgets,
reasoning settings, fresh isolated sessions and single-trial concurrency. Count
failures and limits without replacement trials or hints. Retain observable
usage and actual charges separately from unknown subscription cost. Compare
financial reasoning, implementation and delivery failures separately.

No calibration of these two tasks has been executed. Independent human
financial/source review and external-user validation remain pending. SEC
indenture HTML could be inspected through primary URLs but original bytes were
not captured, so only the factual extracts carry hashes for those documents.
Published references and source history preclude a contamination-free claim.
