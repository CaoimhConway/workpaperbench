# Source and authoring review

References were independently recalculated from source context and authored rows
before evaluation. These are software/reference reviews, not external human
validation or empirical submissions.

| Task | Original direct calculation | Changed-input control |
|---|---|---|
| wp01 | Tesla Q1 R&D 2225-1074 = 1151 USD million. Sequential change (1074-1151)/1151 × 100 = -6.689834926%. | 1400 and -14.285714286%. |
| wp02 | Unique eligible events 100+200+600+300 = 1200 token units. The two distinct txa events both contribute. | 130+250+710+370 = 1460. |
| wp03 | July 5 cutoff selects July 1 P1 100 and July 3 P2 120. Growth 20%. The July 10 revision is ineligible. USD valuation absent. | P1 120, P2 150, growth 25%, USD still unavailable. |
| wp04 | Eligible events 100+250+300+0+125 = 775. Per-transaction maxima 250+300+0+125 = 675. Difference 100. One window does not establish a temporal change. | 920, 800, difference 120. |
| wp05 | Export values 200 and 330 give 65%. Same-definition row totals 300 and 330 give 10%. Narrow comparable growth is supported. | Export 260/400 gives 53.846153846%. Row totals 350/400 give 14.285714286%. |
| wp06 | Reported totals 200/400 give 100%. Common population totals 200/200 give 0%. Reported and matched growth differ. Blind tag join gives 400/1000 and an incorrect 150%. | Reported 200/550 gives 175%. Matched 200/250 gives 25%. |
| wp07 | Apple Services Q1 revenue 46984-23867 = 23117 and profit 34646-17809 = 16837 USD million. Margin 16837/23117 × 100 = 72.833845222%. Q2 17809/23867 × 100 = 74.617672938%. Difference 1.783827715 percentage points. | Q1 revenue 24000, profit 17500, margin 72.916666667%, change 1.083333333 percentage points. |
| wp08 | Same observable 775 token units as wp04. Business purpose and account-to-human links are absent, so the two requested derived measures are unavailable. | Observable 920, labels still unavailable. |

Primary filing context: [Tesla June 2024 10-Q](https://www.sec.gov/Archives/edgar/data/1318605/000162828024032662/tsla-20240630.htm)
and [Apple March 2024 10-Q](https://www.sec.gov/Archives/edgar/data/320193/000032019324000069/aapl-20240330.htm).
The Apple quarter is fiscal Q2, not calendar Q1. Profit/revenue calculations retain
precision from whole-million filing amounts rather than subtracting rounded
published margin percentages. Both candidate tables preserve comparative-year
rows as ordinary context.

The dated release catalog gives every publication its own evidence ID. A correct
scalar cited to the late revision fails context. Eligible preliminary history and
coverage annotations are accepted relevant alternatives. The shared synthetic
corpus preserves distinct event identity and an excluded mint in a transaction
that also has eligible transfers, making exclusion order observable.

Valid controls include CTE/subquery wrappers on every task, operand/whole-table
filing citations, exact-event deduplication, latest eligible publication selection,
INTERSECT matched population, scalar-subquery margin calculations and relevant
extra policy context. Wrong controls include constant and table-mention SQL,
blanket refusal, wrong conclusions, all-citation dumping, late revisions, wrong
year, missing-as-zero, transaction deduplication, premature maxima, one-to-many
joins, percent versus percentage points and unsupported payments/human inference.
The changed fixture is a bounded recomputation check, not proof that arbitrary SQL
generalizes to every dataset.

A fresh read-only reviewer inspected only all eight candidate instructions and the
common schema before freeze. It found no numeric answers, worked examples,
record IDs or task-specific reason vocabulary. Claim IDs, units, cutoff and metric
questions are legitimate requirements. It noted that wp04's single-window question
and wp08's logs-versus-purpose/person question can partly cue evidence limits.
These cases do not establish difficult open-world discovery or contamination-free
performance. Source correctness was outside that review's restricted scope.

The final source-first audit found an originally invisible wrong matched-coverage
join: equal tag multiplicities cancel in the original ratio. The wp06 changed
control now varies metadata-row multiplicity for one covered asset as well as
amounts, preserving population and definitions. The bad query still returns 0%
on original data but 22% on changed data instead of the correct 25%. A named
local and native negative control requires rejection. The audit also accepted
wp08 policy:scope alone as a valid explanation of absent purpose/person labels.

A fresh read-only source-first audit independently checked filing context and
arithmetic, source origins, SQL/evidence alternatives, the candidate/verifier
boundary, workflows, and saved development accounting. Its material findings
were the synthetic-origin fallback, shared metadata locators, tag-weight
cancellation and legitimate scope-only conclusion evidence. These were corrected
before evaluation. It then reported no additional material defect. The primary
verification remains the actual local/native tests, with no external human
validation or proof of unrestricted adversarial isolation.
