# Independent-operand control audit

Catalog: `workflow-v11-canonical-2a1d26d1ec5f`. Scorer: `workflow-1.2.1`.
Prior catalog: `workflow-v10-canonical-b514bac2274f`. No model inference.

The bounded audit tried the following eight incorrect implementations. Each
starts from a complete reference submission and changes just one SQL file.
The original JSON, filenames, claims, citations and other queries stay valid.
The [specific fixtures](../../scripts/workflow_dependency_cases.py) retain the
SQL construction and the [isolated verifier record](dependency-validation.json)
binds their artifact hashes and per-table numerical diagnostics.

| Task / calculation | Wrong implementation tried | Old controls | Revision |
| --- | --- | --- | --- |
| c01 subscription gross-profit bridge | Reconstruct subscription costs using observed revenue times the frozen year-specific cost/revenue fraction, using real division | Survives original and all controls | Add 1,000 USD thousand to FY2024 subscription cost and reported total cost, revenue fixed |
| b06 activity ratios | Read live trips and consumers but return frozen quarterly/monthly ratios by year | Survives original and all controls | Add 202 million FY2025 trips, consumers and three-month period fixed |
| b03 apparent revenue/spot volume | Read live revenue and spot volume but return frozen ratios by segment | Survives original and all controls | Add USD 10 billion consumer Q4 spot volume with booked revenue fixed |
| c04 company operating margins | Calculate live operating income but return frozen GAAP/adjusted margins by period | Survives original and all controls | Add USD 100 million operating expense on both bases to Q4 and its annual period, revenue fixed |
| a03 operating margins | Return original RLDC/revenue and adjusted EBITDA/RLDC ratios while keeping amounts live | Rejected numerically by independent disclosure discrepancy | No addition |
| b01 reserve coverage | Return original coverage percentages while keeping reserves and circulation live | Rejected by June cash change and disclosure discrepancy | No addition |
| b05 annual transaction revenue/TPV | Return original annual ratio while keeping annual activity amounts live | Rejected by disclosure discrepancy | No addition |
| c03 incentives/gross revenue | Return original incentive shares while keeping gross/incentives/net amounts live | Rejected by gross/incentive change and disclosure discrepancy | No addition |

The first four each pass every original-input requirement and old control through
the normal submission-to-verdict path. In v11, each fails only its intended new
control and target table, with reason `numeric`. Delivery, evidence, claims,
original numerical tables and all old controls still pass. The complete verifier
also accepts separately written source-based alternatives for all four queries.
These are authored engineering cases, not measured model failures.

The c01 cost perturbation changes subscription profit and total profit together,
so original reconciliation residuals remain zero. Revenue attribution stays fixed.
The b06 activity control changes both requested ratios, leaving financial outputs
fixed. The b03 control preserves the explicit proxy interpretation and changes
only its observed volume denominator. The c04 control changes costs independently
of revenue and preserves the source's one-million rounding residual. It does not
force adjusted expenses to equal a reconstructed exact amount. These coherent
counterfactuals are separate from the retained deliberate disclosure discrepancies.

Independent arithmetic assertions in
[test_workflow_dependency_revision.py](../../tests/test_workflow_dependency_revision.py)
calculate changed values from source numbers without calling the builder.
Untouched rows and outputs use declared numerical tolerances and semantic row
matching. The versioned builder recomputes every output, not only the failing table.

Coverage is bounded to these eight calculations and four shortcut forms. It does
not vary every row, every ratio operand, the period length, or every expense class.
Other plausible shortcuts can remain. In particular, success on a tested aggregate
ratio does not establish coverage for every constituent row or prove arbitrary
financial robustness. No task expansion or general mutation-testing framework is
introduced. Human financial-domain review remains pending.
