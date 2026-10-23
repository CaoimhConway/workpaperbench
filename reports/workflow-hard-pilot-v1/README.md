# Experimental tier software verification

The three development tasks are frozen as `workflow-hard-pilot-v1-canonical-39c72d97a4ed`. The starting checkout was `c9afff4ba933ff3bb98e5357818ac20aff4eb052`. This record concerns reference behavior, reproducibility and grading. It contains no candidate-model results or empirical difficulty claim.

The [design report](../../docs/WORKFLOW_HARD_PILOT.md) explains the additional analytical decisions beyond workflow-v15. The [worked references](../../datasets/workflow-hard-pilot-v1/references) map the calculations to primary-source extracts and distinguish assumptions from observations.

## Results

| Task | Accepted submissions | Rejected submissions | Changed-input databases | Native reference replay |
| --- | ---: | ---: | ---: | --- |
| Ahold comparability | 4 | 10 | 6 | Pass |
| Microsoft cash and assets | 4 | 10 | 7 | Pass |
| Apple identification and bounds | 4 | 9 | 5 | Pass |
| Total | 12 | 29 | 18 | 3 passes |

Each task accepts the reference, a materially different calculation, reordered rows/columns with additional relevant evidence context, and alternate optional notes. Every accepted submission passes the original database and all controls. Optional notes have no semantic score.

The [complete isolated-verifier results](software-verification.json) retain every variant's numerical, claim, evidence, delivery and control outcome, plus native receipt and verdict hashes. Incorrect numerical submissions fail numeric comparisons, rather than incidental syntax or evidence checks. Incorrect claims fail claims, missing or unknown evidence fails evidence, and constant original answers fail control recomputation while retaining correct original numbers.

| Task | Rejected analytical mistakes |
| --- | --- |
| Ahold | Omitted calendar reinstatement, reversed divestment sign, uniform 52/53 scaling, twice-removed extra week, omitted week in the annual bridge, hard-coded zero reconciliation residual |
| Microsoft | Noncash lease recognition counted as cash, lease interest counted as capital cash, reversed payable sign, cash-flow depreciation/amortization/other used as PPE depreciation, double-counted lease amortization, principal substituted for new ROU recognition |
| Apple | Proportional regional product mix, an interior stress value used as the sharp lower bound, revenue-minimizing allocation reused for gross-profit minimization, zero lower loss because allocation is unknown, incorrect percent scale |

Each task also rejects constant original results, a wrong original-dossier claim, missing core support and an unknown evidence ID.

## Independent checks and execution scope

Six focused financial/package checks pass on the supported SQLite 3.45.1 controller, including byte-for-byte reconstruction. Ahold's separately disclosed adjusted FY2015 column and extra-week cancellation check the period logic. Microsoft's gross and accumulated balance bridges independently reproduce the net residuals. Apple's greedy allocation is checked for marginal preservation, feasibility and exchange optimality against vertex enumeration under every control. These check the economic derivations as well as arithmetic.

The existing Harbor runtime-integrity tests pass separately: 7 tests. The focused catalog, grading and experimental tests on the editing host report 21 passed and 2 skips. An additional frozen-scorer contract test passes for omitted rows, duplicate keys, swapped category/period labels, monetary-unit errors and percent scaling across the new tables. Those skips are the Harbor-dependent module and pinned SQLite reconstruction, both exercised successfully on the supported controller. The unchanged workflow-v15 builder check reconstructs all 30 tasks with identity `workflow-v15-canonical-400f60b5b3b6`.

Native submitted-artifact replay uses the supported `grade` path and `VerifiedDockerEnvironment`, followed by a separate pristine verifier. The [materialization record](materialization.json) retains reviewed projections of actual candidate and verifier input checks, bound to original diagnostic hashes. Candidate contexts contain only the Dockerfile and five dossier inputs. References, alternatives, controls, gold and scorer assets stay outside candidate image contexts. The separate verifier reports blocked network, no inference credential and no Docker socket. This is inference-free oracle replay, not model-provider qualification or a claim that native inference credentials are inaccessible to terminal tools.

The scorer and SQL worker are unchanged frozen workflow-1.2.1 assets. SQL runs against original and control databases. Claims remain scoped to the original dossier. Arbitrary feasible witnesses and optional explanatory prose are not exact-matched or semantically verified.

The [calibration recipe](../../config/workflow-hard-pilot-v1-calibration.json) remains unexecuted. Offline comparison confirms the qualified GLM arguments are preserved exactly after separating provider options from shared budgets. The proposed reference model's route and provider arguments remain explicit unresolved fields.

Independent human financial/source review, external-user validation, reference-provider qualification and measured difficulty remain pending. Microsoft residuals retain rounded-source precision and do not identify unreported movements. Apple bounds are sharp only under the authored uncertainty set and stress assumptions. No inference, spending, historical regrading, baseline change or publication is part of this verification.
