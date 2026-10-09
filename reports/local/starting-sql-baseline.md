# Unchanged starting SQL and retained transitions

Current catalog `workflow-v6-canonical-d07b12eebe22`, scorer `workflow-1.2.0`.
**61/90 queries are byte-identical to reference SQL. 61/90 pass original inputs and 61/90 pass original inputs plus every synthetic control.**
Every task has two identical queries except b04, which has three. Byte identity is a file comparison, not independent proof of financial correctness.
Cases requiring no SQL repair under original inputs and all available controls: b04.

SQL-only diagnostics reuse frozen comparison functions, pristine databases and the existing isolated verifier. Claims, citations, evidence and whole-task completion are **unassessed**, with no gold answer.json or fabricated verdicts supplied. Synthetic controls establish behavior on those authored perturbations only.

## Current table baseline

The task column links the frozen task. Files are environment/starting_<table>.sql and solution/<table>.sql. Controls counts exclude original inputs. Failure names and scorer reasons are explicit.

| Task | Table | Byte identical | Original | Controls passed | Failed controls |
| --- | --- | --- | --- | --- | --- |
| [a01](../../datasets/workflow-v6/tasks/a01/instruction.md) | quarter_model | no | fail:rows | 0/3 | scaled_amounts_preserve_ratios:rows, current_quarter_changes_prior_quarter_preserved:rows, irrelevant_later_disclosure:rows |
| [a01](../../datasets/workflow-v6/tasks/a01/instruction.md) | quarter_reconciliation | yes | pass | 3/3 | - |
| [a01](../../datasets/workflow-v6/tasks/a01/instruction.md) | guidance_bridge | yes | pass | 3/3 | - |
| [a02](../../datasets/workflow-v6/tasks/a02/instruction.md) | cash_model | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, capital_spending_mix_changes_fcf_preserved:numeric, irrelevant_later_disclosure:numeric, independent_disclosure_discrepancy:numeric |
| [a02](../../datasets/workflow-v6/tasks/a02/instruction.md) | operating_cash_bridge | yes | pass | 4/4 | - |
| [a02](../../datasets/workflow-v6/tasks/a02/instruction.md) | segment_model | yes | pass | 4/4 | - |
| [a03](../../datasets/workflow-v6/tasks/a03/instruction.md) | expense_model | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, excluded_payroll_increase_new_expense_unchanged:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [a03](../../datasets/workflow-v6/tasks/a03/instruction.md) | operating_margins | yes | pass | 4/4 | - |
| [a03](../../datasets/workflow-v6/tasks/a03/instruction.md) | definition_attribution | yes | pass | 4/4 | - |
| [a04](../../datasets/workflow-v6/tasks/a04/instruction.md) | cash_generation | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, gross_spending_and_incentives_net_unchanged:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [a04](../../datasets/workflow-v6/tasks/a04/instruction.md) | cash_movement | yes | pass | 4/4 | - |
| [a04](../../datasets/workflow-v6/tasks/a04/instruction.md) | noncash_capital | yes | pass | 4/4 | - |
| [a05](../../datasets/workflow-v6/tasks/a05/instruction.md) | income_model | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, earned_membership_changes_not_merchandise_margin:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [a05](../../datasets/workflow-v6/tasks/a05/instruction.md) | operating_growth_bridge | yes | pass | 4/4 | - |
| [a05](../../datasets/workflow-v6/tasks/a05/instruction.md) | membership_accrual_bridge | yes | pass | 4/4 | - |
| [a06](../../datasets/workflow-v6/tasks/a06/instruction.md) | income_model | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, excluded_phonepe_charge_changes_gaap_not_adjusted:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [a06](../../datasets/workflow-v6/tasks/a06/instruction.md) | adjustment_bridge | yes | pass | 4/4 | - |
| [a06](../../datasets/workflow-v6/tasks/a06/instruction.md) | year_to_date_cash | yes | pass | 4/4 | - |
| [a07](../../datasets/workflow-v6/tasks/a07/instruction.md) | gross_profit_bases | yes | pass | 4/4 | - |
| [a07](../../datasets/workflow-v6/tasks/a07/instruction.md) | current_h20_bridge | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, inventory_release_changes_standard_not_excluded_profit:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [a07](../../datasets/workflow-v6/tasks/a07/instruction.md) | cash_generation | yes | pass | 4/4 | - |
| [a08](../../datasets/workflow-v6/tasks/a08/instruction.md) | income_model | yes | pass | 4/4 | - |
| [a08](../../datasets/workflow-v6/tasks/a08/instruction.md) | operating_adjustment_bridge | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, overlapping_sbc_label_is_not_an_extra_exclusion:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [a08](../../datasets/workflow-v6/tasks/a08/instruction.md) | acquisition_scope | yes | pass | 4/4 | - |
| [a09](../../datasets/workflow-v6/tasks/a09/instruction.md) | segment_model | yes | pass | 4/4 | - |
| [a09](../../datasets/workflow-v6/tasks/a09/instruction.md) | consolidated_bridge | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, corporate_charge_changes_gaap_not_segment_results:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [a09](../../datasets/workflow-v6/tasks/a09/instruction.md) | service_subscriptions | yes | pass | 4/4 | - |
| [a10](../../datasets/workflow-v6/tasks/a10/instruction.md) | income_model | yes | pass | 4/4 | - |
| [a10](../../datasets/workflow-v6/tasks/a10/instruction.md) | currency_and_network | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, fee_and_expense_change_preserves_net_income:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [a10](../../datasets/workflow-v6/tasks/a10/instruction.md) | revenue_growth_bridge | yes | pass | 4/4 | - |
| [b01](../../datasets/workflow-v6/tasks/b01/instruction.md) | reserve_coverage | no | fail:numeric | 0/5 | scaled_amounts_preserve_ratios:numeric, june_cash_and_total_reserves_change:numeric, identical_export_duplicate:numeric, distinct_dates_with_equal_amounts:numeric, independent_disclosure_discrepancy:numeric |
| [b01](../../datasets/workflow-v6/tasks/b01/instruction.md) | signature_lag | yes | pass | 5/5 | - |
| [b01](../../datasets/workflow-v6/tasks/b01/instruction.md) | reserve_bridge | yes | pass | 5/5 | - |
| [b02](../../datasets/workflow-v6/tasks/b02/instruction.md) | qualified_coverage | yes | pass | 5/5 | - |
| [b02](../../datasets/workflow-v6/tasks/b02/instruction.md) | treasury_valuation | no | fail:numeric | 0/5 | scaled_amounts_preserve_ratios:numeric, valuation_change_reconciles:numeric, identical_export_is_one_holding:numeric, distinct_equal_value_holdings_remain:numeric, independent_disclosure_discrepancy:numeric |
| [b02](../../datasets/workflow-v6/tasks/b02/instruction.md) | stock_bridge | yes | pass | 5/5 | - |
| [b03](../../datasets/workflow-v6/tasks/b03/instruction.md) | annual_revenue_bridge | yes | pass | 3/3 | - |
| [b03](../../datasets/workflow-v6/tasks/b03/instruction.md) | spot_revenue_proxy | yes | pass | 3/3 | - |
| [b03](../../datasets/workflow-v6/tasks/b03/instruction.md) | usdc_booked_ratio | no | fail:numeric | 0/3 | scaled_amounts_preserve_ratios:numeric, platform_balance_mix_changes_scoped_ratios:numeric, irrelevant_later_disclosures:numeric |
| [b04](../../datasets/workflow-v6/tasks/b04/instruction.md) | expense_audit | yes | pass | 4/4 | - |
| [b04](../../datasets/workflow-v6/tasks/b04/instruction.md) | annual_revenue_bridge | yes | pass | 4/4 | - |
| [b04](../../datasets/workflow-v6/tasks/b04/instruction.md) | crypto_scope | yes | pass | 4/4 | - |
| [b05](../../datasets/workflow-v6/tasks/b05/instruction.md) | quarter_activity | yes | pass | 4/4 | - |
| [b05](../../datasets/workflow-v6/tasks/b05/instruction.md) | margin_reconciliation | yes | pass | 4/4 | - |
| [b05](../../datasets/workflow-v6/tasks/b05/instruction.md) | annual_activity_bridge | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, customer_interest_changes_tm_not_ex_interest:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [b06](../../datasets/workflow-v6/tasks/b06/instruction.md) | segment_metrics | yes | pass | 4/4 | - |
| [b06](../../datasets/workflow-v6/tasks/b06/instruction.md) | corporate_bridge | yes | pass | 4/4 | - |
| [b06](../../datasets/workflow-v6/tasks/b06/instruction.md) | consumer_activity | no | fail:numeric | 0/4 | scaled_observations_preserve_ratios:numeric, corporate_cost_changes_total_not_segments:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [b07](../../datasets/workflow-v6/tasks/b07/instruction.md) | booking_ratios | yes | pass | 4/4 | - |
| [b07](../../datasets/workflow-v6/tasks/b07/instruction.md) | quarter_cash | yes | pass | 4/4 | - |
| [b07](../../datasets/workflow-v6/tasks/b07/instruction.md) | rolling_cash | no | fail:numeric | 0/4 | scaled_observations_preserve_ratios:numeric, one_quarter_cash_changes_each_applicable_window:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [b08](../../datasets/workflow-v6/tasks/b08/instruction.md) | category_economics | yes | pass | 4/4 | - |
| [b08](../../datasets/workflow-v6/tasks/b08/instruction.md) | cash_generation | yes | pass | 4/4 | - |
| [b08](../../datasets/workflow-v6/tasks/b08/instruction.md) | subscription_stock_bridge | no | fail:numeric | 0/4 | scaled_observations_preserve_ratios:numeric, subscription_revenue_and_cost_change_preserve_profit:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [b09](../../datasets/workflow-v6/tasks/b09/instruction.md) | operating_reconciliation | no | fail:numeric | 0/4 | scaled_income_and_matching_denominators:numeric, asset_gain_changes_gaap_income_not_operating_or_adjusted_income:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [b09](../../datasets/workflow-v6/tasks/b09/instruction.md) | income_reconciliation | yes | pass | 4/4 | - |
| [b09](../../datasets/workflow-v6/tasks/b09/instruction.md) | share_basis | yes | pass | 4/4 | - |
| [b10](../../datasets/workflow-v6/tasks/b10/instruction.md) | parent_earnings_bridge | yes | pass | 4/4 | - |
| [b10](../../datasets/workflow-v6/tasks/b10/instruction.md) | consolidated_cash_bridge | no | fail:numeric | 0/4 | scaled_income_and_matching_denominators:numeric, noncontrolling_income_changes_consolidated_not_parent_scope:numeric, irrelevant_later_periods:numeric, independent_disclosure_discrepancy:numeric |
| [b10](../../datasets/workflow-v6/tasks/b10/instruction.md) | investment_gain_bridge | yes | pass | 4/4 | - |
| [c01](../../datasets/workflow-v6/tasks/c01/instruction.md) | revenue_bridge | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, bitcoin_revenue_and_cost_change_with_matching_totals:numeric, irrelevant_later_disclosure:numeric, independent_disclosure_discrepancy:numeric |
| [c01](../../datasets/workflow-v6/tasks/c01/instruction.md) | profit_bridge | yes | pass | 4/4 | - |
| [c01](../../datasets/workflow-v6/tasks/c01/instruction.md) | reconciliation | yes | pass | 4/4 | - |
| [c02](../../datasets/workflow-v6/tasks/c02/instruction.md) | operating_reconciliation | yes | pass | 4/4 | - |
| [c02](../../datasets/workflow-v6/tasks/c02/instruction.md) | adjustment_attribution | yes | pass | 4/4 | - |
| [c02](../../datasets/workflow-v6/tasks/c02/instruction.md) | arr_guidance_bridge | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, prior_acquisition_adjustment_changes_attribution:numeric, irrelevant_later_disclosure:numeric, independent_disclosure_discrepancy:numeric |
| [c03](../../datasets/workflow-v6/tasks/c03/instruction.md) | gross_to_net | no | fail:numeric | 0/4 | scaled_amounts_preserve_ratios:numeric, gross_and_incentive_increase_net_unchanged:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [c03](../../datasets/workflow-v6/tasks/c03/instruction.md) | net_income_reconciliation | yes | pass | 4/4 | - |
| [c03](../../datasets/workflow-v6/tasks/c03/instruction.md) | income_growth_bridge | yes | pass | 4/4 | - |
| [c04](../../datasets/workflow-v6/tasks/c04/instruction.md) | regional_attribution | no | fail:numeric | 0/3 | scaled_amounts_preserve_ratios:numeric, regional_mix_changes_worldwide_unchanged:numeric, irrelevant_later_disclosures:numeric |
| [c04](../../datasets/workflow-v6/tasks/c04/instruction.md) | worldwide_reconciliation | yes | pass | 3/3 | - |
| [c04](../../datasets/workflow-v6/tasks/c04/instruction.md) | company_margin_bridge | yes | pass | 3/3 | - |
| [c05](../../datasets/workflow-v6/tasks/c05/instruction.md) | category_margin | yes | pass | 4/4 | - |
| [c05](../../datasets/workflow-v6/tasks/c05/instruction.md) | net_income_growth_bridge | yes | pass | 4/4 | - |
| [c05](../../datasets/workflow-v6/tasks/c05/instruction.md) | prior_tax_baseline | no | fail:numeric | 0/4 | scaled_financial_observations:numeric, prior_tax_charge_changes_gaap_not_adjusted_baseline:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [c06](../../datasets/workflow-v6/tasks/c06/instruction.md) | geographic_currency | yes | pass | 4/4 | - |
| [c06](../../datasets/workflow-v6/tasks/c06/instruction.md) | consolidated_currency_bridge | no | fail:numeric | 0/4 | scaled_financial_observations:numeric, currency_translation_changes_reported_not_cc:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [c06](../../datasets/workflow-v6/tasks/c06/instruction.md) | revenue_growth_components | yes | pass | 4/4 | - |
| [c07](../../datasets/workflow-v6/tasks/c07/instruction.md) | financial_versions | yes | pass | 4/4 | - |
| [c07](../../datasets/workflow-v6/tasks/c07/instruction.md) | settlement_revision_bridge | no | fail:numeric | 0/4 | scaled_financial_observations:numeric, expense_and_tax_revision_preserves_total_cash:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [c07](../../datasets/workflow-v6/tasks/c07/instruction.md) | cash_revision_bridge | yes | pass | 4/4 | - |
| [c08](../../datasets/workflow-v6/tasks/c08/instruction.md) | income_reconciliation | yes | pass | 4/4 | - |
| [c08](../../datasets/workflow-v6/tasks/c08/instruction.md) | share_basis | no | fail:numeric | 0/4 | scaled_financials_and_matching_denominators:numeric, gaap_tax_benefit_changes_not_adjusted_income:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [c08](../../datasets/workflow-v6/tasks/c08/instruction.md) | segment_growth_bridge | yes | pass | 4/4 | - |
| [c09](../../datasets/workflow-v6/tasks/c09/instruction.md) | bank_basis_bridge | no | fail:numeric | 0/4 | scaled_financials_and_matching_denominators:numeric, fte_presentation_changes_reported_estimate_not_managed_ratios:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |
| [c09](../../datasets/workflow-v6/tasks/c09/instruction.md) | significant_item_bridge | yes | pass | 4/4 | - |
| [c09](../../datasets/workflow-v6/tasks/c09/instruction.md) | annual_exclusion_components | yes | pass | 4/4 | - |
| [c10](../../datasets/workflow-v6/tasks/c10/instruction.md) | regional_currency | yes | pass | 4/4 | - |
| [c10](../../datasets/workflow-v6/tasks/c10/instruction.md) | annual_currency_margin | yes | pass | 4/4 | - |
| [c10](../../datasets/workflow-v6/tasks/c10/instruction.md) | forecast_bounds | no | fail:numeric | 0/4 | scaled_financials_and_matching_denominators:numeric, included_forecast_cost_is_not_added_back:numeric, irrelevant_later_disclosures:numeric, independent_disclosure_discrepancy:numeric |

## Retained model transitions

Repair = incorrect to correct, Preservation = correct to correct, Regression = correct to incorrect, Unrepaired = incorrect to incorrect. Classify original-input correctness separately from correctness on original inputs plus every control. Each comparison uses one frozen task/scorer on both sides.
Corrected workflow-v5 replays are separate from original workflow-v5 scores and are not workflow-v6 model results. Changes between scorer versions are scorer corrections, not model repairs. Original submissions, scores and correction receipts remain unchanged.

| Attempt / scoring view | Table | Starting original / controls | Submitted original / controls | Original transition | All-input transition |
| --- | --- | --- | --- | --- | --- |
| qwen36-development-a01-5 / workflow-v5 original | quarter_model | False / 0/3 | True / 3/3 | Repair | Repair |
| qwen36-development-a01-5 / workflow-v5 original | quarter_reconciliation | True / 3/3 | False / 0/3 | Regression | Regression |
| qwen36-development-a01-5 / workflow-v5 original | guidance_bridge | True / 3/3 | True / 3/3 | Preservation | Preservation |
| qwen36-development-a01-5 / workflow-v5 corrected | quarter_model | False / 0/3 | True / 3/3 | Repair | Repair |
| qwen36-development-a01-5 / workflow-v5 corrected | quarter_reconciliation | True / 3/3 | False / 0/3 | Regression | Regression |
| qwen36-development-a01-5 / workflow-v5 corrected | guidance_bridge | True / 3/3 | True / 3/3 | Preservation | Preservation |
| qwen36-development-b01-1 / workflow-v5 original | reserve_coverage | False / 0/5 | True / 4/5 | Repair | Unrepaired |
| qwen36-development-b01-1 / workflow-v5 original | signature_lag | True / 5/5 | True / 5/5 | Preservation | Preservation |
| qwen36-development-b01-1 / workflow-v5 original | reserve_bridge | True / 5/5 | True / 5/5 | Preservation | Preservation |
| qwen36-development-b01-1 / workflow-v5 corrected | reserve_coverage | False / 0/5 | True / 4/5 | Repair | Unrepaired |
| qwen36-development-b01-1 / workflow-v5 corrected | signature_lag | True / 5/5 | True / 5/5 | Preservation | Preservation |
| qwen36-development-b01-1 / workflow-v5 corrected | reserve_bridge | True / 5/5 | True / 5/5 | Preservation | Preservation |
| qwen36-development-c01-5 / workflow-v5 original | revenue_bridge | False / 0/4 | False / 0/4 | Unrepaired | Unrepaired |
| qwen36-development-c01-5 / workflow-v5 original | profit_bridge | True / 4/4 | False / 0/4 | Regression | Regression |
| qwen36-development-c01-5 / workflow-v5 original | reconciliation | True / 4/4 | True / 4/4 | Preservation | Preservation |
| qwen36-development-c01-5 / workflow-v5 corrected | revenue_bridge | False / 0/4 | True / 4/4 | Repair | Repair |
| qwen36-development-c01-5 / workflow-v5 corrected | profit_bridge | True / 4/4 | True / 4/4 | Preservation | Preservation |
| qwen36-development-c01-5 / workflow-v5 corrected | reconciliation | True / 4/4 | True / 4/4 | Preservation | Preservation |
| local-budget-development-b01-1 / workflow-v4 original | reserve_coverage | False / 0/4 | True / 3/4 | Repair | Unrepaired |
| local-budget-development-b01-1 / workflow-v4 original | signature_lag | True / 4/4 | True / 3/4 | Preservation | Regression |
| local-budget-development-b01-1 / workflow-v4 original | reserve_bridge | True / 4/4 | True / 3/4 | Preservation | Regression |

| Scoring view / scope | Repair | Preservation | Regression | Unrepaired |
| --- | --- | --- | --- | --- |
| workflow-v5/original / original inputs | 2 | 4 | 2 | 1 |
| workflow-v5/original / all inputs | 1 | 4 | 2 | 2 |
| workflow-v5/corrected / original inputs | 3 | 5 | 1 | 0 |
| workflow-v5/corrected / all inputs | 2 | 5 | 1 | 1 |
| workflow-v4/original / original inputs | 1 | 2 | 0 | 0 |
| workflow-v4/original / all inputs | 0 | 0 | 2 | 1 |

The Microsoft basis-point query and Brale duplicate-export defect remain in the retained answers. The Block label correction changes acceptance without changing its SQL. The earlier workflow-v4 Brale delivery is reported under its original scorer.
Incomplete deliveries, timeouts, interrupted and partial attempts lack comparable complete-delivery table verdicts and are unclassified here, rather than counted as incorrect SQL. See the [original development diagnostics](../local/workflow-development-diagnostics-1.json), [budget diagnostics](../local/workflow-development-budget-diagnostics-1.json), [hybrid diagnostics](../local/workflow-development-hybrid-diagnostics-1.json), [Qwen pilot](../local/workflow-qwen36-development-1.json), and [interrupted attempt](../local/workflow-qwen36-development-2-interrupted.json). Partial-query scoring and aggregation across unequal budgets are questions for deeper review.

## Reproduction and provenance

No inference or external service spending. Execution: Mac Pro, dedicated workpaperbench-local Linux guest. Containers use network none, read-only root, 384 MiB memory, one CPU, 32 PIDs, dropped capabilities, no-new-privileges and bounded tmpfs. Frozen SQL workers enforce the existing time, memory, read-only SQL and output limits. Every receipt passed all four existing isolation probes.
Reproduce from the published revision with the documented [local verifier setup](../../docs/WORKFLOW.md):

```sh
.venv/bin/python scripts/starting_sql_baseline.py --output /tmp/starting-sql-baseline.md
```

Report implementation base: `9844d259520b87f8c6b563cf1ba92e5a04a9b4e5`.
Generator SHA256: `edff7f287de8c35195797c987a30c8aba908398de822d6e6398015eeda7a6b67`.
Verifier helper SHA256: `2eac7145e1db3b6504066deb05e4a7cbac8ab205a74941646094fce429ec2a1d`.
Container program SHA256: `26cbb153d2e0ecd9d7af7afeade622c2690c52f67e973789e7e05c159fd1f6f0`.
Current manifest SHA256: `a2b0105d7d35629df1a3d1a94450b4b8bb80c37be935f92b0f100a9c016802f9`.
Current scorer SHA256: `fe823e2c8adbc5ca556e0900d1eb61275ba5101a910421f6a7b304579a33f35e`.
Corrected replay SHA256: `9f6c90868c745c3787661bab488c93eb9c9c40d0fd6b53a25242288afd71508e`.

Historical catalogs: [workflow-v4](../../datasets/workflow-v4/manifest.json), [workflow-v5](../../datasets/workflow-v5/manifest.json). Corrected tasks are reconstructed by reviewed_task, preserving original inputs and starting SQL. [Corrected replay](../workflow-v5/corrected-replay.json) binds task hashes, submitted file hashes and original receipt hashes. The budget diagnostic binds the earlier receipt and SQL hashes. Task tree hashes below authenticate all starting/reference SQL, original and synthetic inputs, verifier code and gold expectations. Image IDs identify the executed verifier builds.

| Baseline task / view | Task tree SHA256 | Verifier image |
| --- | --- | --- |
| workflow-v6/a01 | d0b28fee894032ea9724834c98c488138bd65793ff04b798be39e2d604a1cc5d | sha256:6a6e79241a2a0ec475db9402b64dbda456c665736fda0fc910da59b2220d08fe |
| workflow-v6/a02 | 74bc902a004e57ade277f1cf9f03c3e214f1e849ad964db864126eb602e04937 | sha256:759a9e07f83523c105552e2ab591cd487da970e3e55de748e37e0b46eff9c700 |
| workflow-v6/a03 | 01626c9e46e01c97ed797468204ae870044905d55794ebb7120751a6da71a4c7 | sha256:019b9697566026e0964f61f7836e9e853b21e39880c7df60f9cdb802e25901bc |
| workflow-v6/a04 | 08c87475d5dfc34c7d4829ad25aed478f55671d7d23ea70dfaa95a2934907a52 | sha256:dddd9a8546010e3eb83890823c91d39b297685866206550ddadf3c0b687cc55b |
| workflow-v6/a05 | 7882e2b7192ae5316638d8ca392851b995bce2c3b82989655e255b4c31553d89 | sha256:9ce6505d2649abc9c1e6b6d6f3c954b043a7b9515f477b51a99027931529aeac |
| workflow-v6/a06 | 80aae5815b20ee9daed99549fd3dae30c1d8203661cc671dccb42e8893d2047a | sha256:447dd6116d73169848d2c8e25d665b9641b8d5b589add1aaf24b40cb903ef3c6 |
| workflow-v6/a07 | 2db59e441dfedf515796a4c22cc9fb1f77ce751433568d67fb91790fbaf2ea81 | sha256:9ce4130cd0c95c59e9858d1e93bec14c4456457b0ff10d0d7f4a585d8c9847ec |
| workflow-v6/a08 | 616e0d1ed6227ac170b37a571af71453347a19295f740848200a73d38ec063ce | sha256:933f368ba2f6b346fa4003e6306155842b85db75dc0ab97abcd83f7ad6c42f18 |
| workflow-v6/a09 | 8cddc8372e963820fb1f491dee8d80ffd1f1d05cfd22545cbb473101e9515609 | sha256:2ef9a8ba6f5295befe1b4120544f521d3a2eaa97767fc3658b134a07def09048 |
| workflow-v6/a10 | 193e148ca6884c065c59417d7c0afbd3deae804fb82630b3f6c1c58bc693a16c | sha256:7df4532cc81973f7760e7657772f50131ee17f0efae5879e1232f2d44d58bff6 |
| workflow-v6/b01 | 2eaaa268e6eceb90de67365f5ad07830d1c81551767f6a8d2329165dcc93b688 | sha256:f06377c940a18b9da89db3864d8616b9ec3c35177f5258d0a9090cc461c7c3ba |
| workflow-v6/b02 | f6ee0fbe8707fb4c2f45e9385985999a1f8ebdc2f8b939285a6b2c9c78c1d663 | sha256:ef99450e9aab774fa75eec9de57919faab8e06ce42da52810180f2b6f6ba3a93 |
| workflow-v6/b03 | bc1fe68d249b8b1470f31e97bbf02be8e1904b3b3e591b56401d35fcc735ed8d | sha256:d79779de285fa6703f8c0ee9abee3c78196d71b04a1b113606fb16101fc6fd15 |
| workflow-v6/b04 | e448e33f31f3aed6c893b0fb88302158cf7c3df96615b1a6bf219fea1eb35bb8 | sha256:af3f3375a2a0f053e7b90e68a53cbdc5d434ba04a52dbd2ee49415bb46dba8fd |
| workflow-v6/b05 | c1b3f07ccbb2b7ba638e9fa5dd60bbd2f60675dfce7325c3d18d7b0b321d1187 | sha256:67db9e4f356d62332a99f0fa27abefd47cc2598c67173a4e1d0c1430525fe219 |
| workflow-v6/b06 | c0d7a25b97343fe1af263402824c52a2a10f9b8a1ff43c9889955e4de9ffa6f5 | sha256:b76a60e16f61f687d556e4a486e04685ba72b22b5828cd3f348fb604b1ece3b8 |
| workflow-v6/b07 | 9e0e36daf4f28c19d0670a6fdc7ae54adae4c3a0231200f864c35e489cfc4035 | sha256:bbc74b9a2d7dd290965d0272162c6853a59f0ff9fccce50e8ffd28990643f052 |
| workflow-v6/b08 | ff55549c794ce021db545ced8c15bf47e1e758e1c5ee23bc74058021a01f5f13 | sha256:bd722ff6a2ffc5d4aaae08a4b754f75a18862b08fbc2fa46f7ab49ee3891cdc7 |
| workflow-v6/b09 | fa5e7098707693d12fe0469d7ffd01e43e1b048b9cf22a7f85418f503fa1f555 | sha256:37d5869fd9e14d6ea2fd1e567a3e22327040ee7cb228df5912fb15ce4d883608 |
| workflow-v6/b10 | 97a6888046dfebe8c82f9cdd9a7fd2ecadb3ffa08faded657717387578982ea6 | sha256:8c3c66974b7975a9c236d569829a7e109a7365f225a82a10c0fadaa3752c6942 |
| workflow-v6/c01 | e322f168198fb8146a10873fa1eb2897fa779ad442e185589d4ada39b132a989 | sha256:9a958eb76dcf3216dd5286d8d4406e9cd5e7925da4e6ca66fb528900e165aa52 |
| workflow-v6/c02 | c7a1cc2fb79f000f5eacb2b6390bf25a240027e0b40cd14b48059686e19c4c39 | sha256:53f9a1238967b6c14c290802736d37b2b7d6bced2b4b58b5a8dce5bbe3a3c2cf |
| workflow-v6/c03 | ef6c0e71e74576ff97711997d336a370b4103d92a3a9490b549c07ef2e5d0663 | sha256:ffadd7a60c570772c2aad45dc3f81f9cfb9e005444c45f5ea14ab6a022180e17 |
| workflow-v6/c04 | e9c996752cca052bd22a2b4bf523bcf65f9b51a5389a6d1e69c623007a5aa919 | sha256:5f6aaf7ff039e98d550970b6162cd16152d9fbda792b085673c23023fd835b86 |
| workflow-v6/c05 | fa8d62b59167e0868c946f58e124b09dc83a9324723ffbe233b54198b378de0b | sha256:afa9260fb3edc25710c9ec2bb1bb7993a18d27f67af33d1299b3547a2d8ee36f |
| workflow-v6/c06 | f5a309b057da10893f1f6b0bf032f4c0ab146e0243e8c3bc9248a89513faf1e0 | sha256:6de3ee4f158ba6fddf31af7284900ad05c9080b93ff9264de33bcfa73dfb2057 |
| workflow-v6/c07 | 7dbdff618f2407726aae145d06d9dd4c745ec5477f9e99fbfbabd0a22cf4c692 | sha256:51f38cb5c92b300c8e344ab7aca2e4d60bde8e9a93948e7e9c6b3dc55eb263ae |
| workflow-v6/c08 | 57cb27cea7cab5b6dec21f15724dc906ee5c3da963096efe5560c3926f846693 | sha256:5c7a48cb594dd8554081069a787cc409b21ff4dd52f5f3c32632180d58bb5779 |
| workflow-v6/c09 | bb83863bbc87d28b698da47f1b3c00ef13da773b442ca85ecfd267944d7c0834 | sha256:9d1057b23459370ff2fa32493845570934f95856aa8d8da505cc393cfe9b0fc8 |
| workflow-v6/c10 | 6eb6ac44e256131f73945f613a3e5fcb71948b7072e4cd84054c1ebad451a2e6 | sha256:937415148a34c5a849e687dfa8b66e9fcd8d61d4620c858c04af79bd19241840 |
| workflow-v4/b01 | 54ce0f2a2b0075355136165b785601716b89e389165f23c2c5e1a8e22c172ce0 | sha256:e4ec39ab3ce726a4afbcd2dfb327a935b7dcf694459318991b87b54af1705bd9 |
| workflow-v5/a01 | dcaefcc8fd9c21b22937260c8e77d68cf364606d6c2e2ba9934f89f4e3983e59 | sha256:5cf31b5eaf0c73b806bc05c45d815d7b8c688107a213ac58458683f4dcf8be33 |
| workflow-v5/a01-corrected | d119a601f18a28c2bfe994480e64813f0fffb0aeb1cabe21bdc323d7193efd50 | sha256:cc8def8a0691eb9a88b109ed4a906742df5bd73f0646fe33171f7c4136d9dd8d |
| workflow-v5/b01 | c3adad399c0fc576ede83cd073656546752f7e5aba81452226acd9324e9604ee | sha256:9ad170378614bc75c735a5b9c4bc109f13f20d9c9b062463ba08967ebcffb6e1 |
| workflow-v5/b01-corrected | cfb36e5971656c4c932b574e3461ae6a3ab478c1066871c4f9a259d2e1e14ffb | sha256:8e5a5c72863e7e52ccdf9a4e66b159789c78908ce7276c2a57e718a0d48e471c |
| workflow-v5/c01 | ca99d37c4bae432e9cfa2b65314f48dbb4017646874fc6a7dff262c566f4cff3 | sha256:447d192f35351500ede3e0361dab50f967394187eac34ce98009dce2cafb28c7 |
| workflow-v5/c01-corrected | 0b08b2be6f809838ed6519e2fc34715b8e3a9ba9c68ccb2c9eb84b45d73a628a | sha256:4943942e7483d61ed4272ce4a7b79bb2f83366b1b851b973608d96ff96c8223f |

These are bounded engineering diagnostics. They do not establish claim correctness, whole-task success, human agreement, independent domain validation or model performance on workflow-v6. The high starting-correct fraction and the no-repair case should inform the deeper methodology review without changing the tasks or grader in this pass.
