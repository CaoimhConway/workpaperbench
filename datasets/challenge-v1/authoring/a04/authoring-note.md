# a04 private authoring note

Decision: assess an expected-currency guidance comparison separately from after-tax profitability. The guidance PDF explicitly excludes0.02 expected favorable currency impact from its constant-currency non-GAAP values, so the analyst request defines the target including that adjustment. Rebuild high1.04+0.21+0.01+0.40+0.01-0.21+0.02=1.48. Reported actual1.47 gives-0.01. Do not claim this is an independently observed actual constant-currency EPS. Select quarterly not half-year adjustment amounts, add four excluded expenses1170+591+31+84=1876, then subtract the increase820 in tax expense to obtain1056 and3151+1056=4207. Wrong approaches add tax expense, copy the subtotal, use half-year values, or compare nominal actual to a constant-currency-only target. Coherent scale control doubles monetary values but leaves EPS and guidance unchanged, the tax control adds100 to both quarter and cumulative tax adjustments while reported comparison rows intentionally stay unreconciled, and the guidance compensation change affects only the earlier forecast. All requested numeric claims change in at least one control. At least guidance plus later reconciliation and income sections are needed. No source field supplies all independent derivations, and no always-abstain shortcut. Source-first verification found the PDF currency footnote before evaluation exposure.

## Independent Decimal calculation

{
  "guidance_upper": "1.48",
  "eps_gap": "-0.01",
  "net_income_adjustment": "1056",
  "adjusted_net_income": "4207",
  "adjusted_net_margin": "29.92389216871754747848353368"
}

## Synthetic controls

compatible_monetary_scale: {"adjusted_net_income": 8414.0, "adjusted_net_margin": 29.923892168717547, "eps_gap": -0.01, "guidance_upper": 1.48, "net_income_adjustment": 2112.0}

tax_adjustment_gap: {"adjusted_net_income": 4107.0, "adjusted_net_margin": 29.21260402589089, "eps_gap": -0.01, "guidance_upper": 1.48, "net_income_adjustment": 956.0}

guidance_compensation_change: {"adjusted_net_income": 4207.0, "adjusted_net_margin": 29.923892168717547, "eps_gap": -0.06, "guidance_upper": 1.53, "net_income_adjustment": 1056.0}

Reference SQL is authored, not a model submission. All counterfactual observations are synthetic. No candidate SQL is executed locally. Native execution, equivalent-method checks and hostile controls run separately in hosted Actions.

Independent source-first review verified source response and extract hashes, all original Decimal gold and nine control expected values. Review corrected equivalent revenue and consolidated segment-total support paths, Oracle adjusted-value locators and inapplicable timestamp caveats before exposure. It is not a claim of human review.
