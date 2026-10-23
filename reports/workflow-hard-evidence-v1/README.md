# Sufficient evidence paths for the evaluation supplement

Manifest `workflow-hard-eval-v1-canonical-372b3270ea4b` corrects two false
citation rejections in the four-task supplement. It preserves all candidate
inputs, numerical answers, controls, claim verdicts, financial rules and worker
limits. The [package comparison](package-comparison.json) confirms that only
the two affected task gold files change, each by one added evidence path.
The frozen financial scorer and the v15 baseline are unchanged.

For BMS `performance_views`, s05+s06+s08 suffice. The earnings disclosure
provides the IPRD and award expenses, actual revenues, pretax result and
contingent-consideration effect. The pro forma disclosure supplies the revenue
comparator. The authored scope defines the selected-effects diagnostic. Requiring
the redundant acquisition-note locator s02 rejects a supported calculation.

For Constellation `retained_interest_bridge`, s02+s05 suffice. The transfer,
collection and beginning/ending balance disclosures establish the bridge.
The authored cash-flow presentation locator s07 is not needed for this stock
reconciliation. Requiring it rejects a sufficient factual path.

Both corrections were independently checked against the source facts after
all final model outputs were inspected. They repair evidence selection, with
no changes to candidate submissions. The numerical Sol c01 rejection remains:
the 43 discount on sales is not identified as an additional reduction of the
separately disclosed noncash DPP addition. DeepSeek b01 still lacks necessary
transaction citations for its other two tables.

The [protocol](../../config/hard-evaluation-20261023-r2/evidence-reassessment.json)
includes all twelve scheduled submissions. Original and worker-only scores
remain separate from the [corrected reassessment](../hard-evaluation-20261023-r2/evidence-reassessment.json).
Delivery failures keep their original complete verdict, since SQL and evidence
evaluation were not reached. No repaired delivery, new model attempt or
outcome-dependent inclusion is permitted.

Seven focused Linux package tests pass, including reproducible construction,
reference/alternative calculations and two citation regressions that accept the
sufficient paths while rejecting missing required disclosures. Broader worker
and native-reference verification from the [SQL correction](../workflow-hard-sql-1.0.1/README.md)
remains applicable because the worker and submitted reference files are unchanged.

All 69 isolated variants pass their expected outcomes: 20 legitimate workpapers
are accepted and 49 targeted incorrect workpapers are rejected. The unchanged
submissions also complete eight native isolated replays, with forty matching
runtime materialization proofs. Four delivery failures retain their original
verdicts. [Verification](verification.json) and the [summary](summary.json) bind
these checks to the corrected package identity. No inference or external-service
spending was involved.
