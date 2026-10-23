# Harder-tier development calibration

Six fresh attempts cover two development tasks from `workflow-hard-pilot-v2`,
with one attempt per task and configuration. The original receipts report two
strict completions out of six. That count includes a verifier compatibility
failure and unnecessarily restrictive evidence paths, so it is not a financial
reasoning pass rate or evidence of general benchmark difficulty. No historical
receipt, submitted workpaper or official score is changed by this analysis.

| Configuration | Task | Official score | Observed failure classification |
| --- | --- | ---: | --- |
| GLM | a01 | 0 | Invalid delivered SQL, turn limit, and one sufficient evidence path rejected |
| GLM | b01 | 0 | Claim 1 lacks necessary scenario evidence, and claim 3 has a sufficient evidence path rejected |
| DeepSeek | a01 | 1 | All original, control, claim and delivery checks passed |
| DeepSeek | b01 | 0 | Incorrect portfolio neutrality thresholds after dilution ordering changes, incomplete claim 1 evidence, and sufficient claim 3 evidence rejected |
| Sol | a01 | 1 | All original, control, claim and delivery checks passed |
| Sol | b01 | 0 | SQL-worker compatibility failure, with an unchanged-submission diagnostic passing under the corrected experimental worker |

All six submissions give the expected original claim verdicts. The receipt
files in [receipts](receipts/) bind task, runtime and workpaper identities.
The corresponding [workpapers](workpapers/) retain the submitted files.
Recorded OpenRouter generation costs total **USD 0.612266335** across the four
paid attempts. Actual subscription charges are unmeasured. Token-equivalent
API prices are not treated as subscription spending.

## Financial and delivery errors

DeepSeek b01 [thresholds.sql](workpapers/hard-development-20261023-deepseek-b01-1/thresholds.sql),
lines 36-41, always places 2027 before 2025. In the `dilution_order` control,
2027 amortization becomes 1.0 million. The incremental earnings-per-share
ratios become 0.9292068038 for 2025 and 1.0836320124 for 2027, reversing the
required order. Independent portfolio EPS intersections give these boundaries:

| Net-income boundary, USD million | Correct | Submitted formula |
| --- | ---: | ---: |
| earnings_2025 | 55.3400773551 | 55.0638986792 |
| earnings_2027 | 64.7075757630 | 64.5370644588 |

This is the intended financial dependency: a neutrality boundary depends on
the other issues already dilutive at that boundary. The submission's
[diluted_eps.sql](workpapers/hard-development-20261023-deepseek-b01-1/diluted_eps.sql)
also fixes the order, but the finite tested income grid does not expose that
error in the EPS table. The threshold control does. Other submitted numerical
tables pass their original and control checks.

GLM a01 [distribution_frontier.sql](workpapers/hard-development-20261023-glm-a01-1/distribution_frontier.sql)
has two column-scope defects. Its `selected` CTE references `bounds.*` without
`FROM bounds`, and its final query selects `raw_upper_limit` from `bounds`
rather than `selected`. The missing alias is a delivered-query error, not
evidence that the intended financial formula is wrong. The receipt records
`turn_limit`. The other two tables pass all numerical controls. No causal
claim is made that the limit caused the SQL error.

## Evidence-path review

GLM a01 claim 3 cites `a01:s02` and `a01:s04`. Both explicitly preserve the
unexplained difference between covenant availability and commitment less
utilisation. They sufficiently support an unresolved currency-attribution
verdict. Requiring `a01:s01` as well is unnecessary for that claim.

GLM and DeepSeek b01 claim 3 cite `b01:s06`. Its scope note explicitly says
the supplied hedge notionals are incomplete and gross note issuance does not
identify net company dilution. This alone supports the unresolved verdict.
Requiring the additional authored-scope citation `b01:s08` rejects a
sufficient path.

The two b01 claim 1 omissions are different. Both omit `b01:s02`, which gives
the coupon and amortization inputs for the frozen full-period numerator
adjustments. DeepSeek also omits `b01:s01`, which provides year-end principal.
The historical aggregate addback and reported diluted count in `b01:s06`
do not alone establish the requested frozen-year-end sensitivity. These are
incomplete claim-local citations even though their table citations contain
the necessary sources. A less restrictive sufficient claim path is
`b01:s01`, `b01:s02`, `b01:s06`, `b01:s08`: proving that at least one note
reduces EPS at price 12 does not require every indenture or a separate
sequencing citation. This observation does not revise the original scores.

## SQL-worker diagnostic and limits

Sol b01 [diluted_eps.sql](workpapers/hard-development-20261023-sol-b01-1/diluted_eps.sql)
enumerates all inclusion subsets and selects the lowest EPS. That construction
is valid for the specified positive-income scenarios. Its line 38 counts
rows in a CTE. A separate isolated, inference-free diagnostic retained every
candidate file and replaced only the copied verifier worker and its copied
integrity binding with the corrected experimental worker. All original,
control, evidence and delivery checks then passed. The diagnostic worker
SHA-256 is
`4103f82f9b3af6fce87f0db2235f581bceee7cabc0ab88822280950e914ec7e4`.
The [diagnostic receipt](sol-worker-diagnostic.json) is retained separately. This establishes a
worker compatibility defect and is not an official corrected score.

The other five attempts have no recorded trial exception. Several paid
requests used output-limit recovery, but the receipts do not establish that
those recoveries caused a financial error. GLM a01 alone reports a trial
turn limit. These six development observations do not establish a stable
configuration ranking, a target pass rate or held-out difficulty. Human
financial review and independent external-user validation remain separate
quality gates.
