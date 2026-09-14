# a03 private authoring note

Decision: separate sequential consolidated profitability from a business-specific guidance comparison. Reconcile quarter versus half-year durations before deriving Q1, form two margins with their matching denominators and compare Azure on the constant-currency basis. Nearby prior-year and segment rows remain, including the recast definition. Wrong approaches include subtracting EPS, comparing H1 to Q2, using gross margin or Intelligent Cloud growth instead of Azure, or nominal guidance mixing. Independent amounts:135217-69632=65585 and62205-31653=30552. Monetary and share scaling preserves EPS and margins. Changed Azure growth preserves zero currency impact. A Q2 R&D reduction100 also reduces H1 expense100, increases quarter/H1 operating, pretax and net income100, updates EPS, leaves Q1 unchanged and changes the Q2-to-Q1 margin. Segment tables are contextual frozen excerpts, not SQL control inputs. No source copy answers derived Q1 and both-period margin gap. Source2+3 are necessary, and1+4 support the separate positive growth comparison.

## Independent Decimal calculation

{
  "q1_revenue": "65585.0",
  "q1_operating_income": "30552.0",
  "margin_change": "-112.6274266716912044988766260",
  "azure_gap": "-1"
}

## Synthetic controls

compatible_monetary_scale: {"azure_gap": -1.0, "margin_change": -112.62742667169121, "q1_operating_income": 61104.0, "q1_revenue": 131170.0}

business_growth_change: {"azure_gap": 1.0, "margin_change": -112.62742667169121, "q1_operating_income": 30552.0, "q1_revenue": 65585.0}

quarter_expense_change: {"azure_gap": -1.0, "margin_change": -98.26621343639708, "q1_operating_income": 30552.0, "q1_revenue": 65585.0}

Reference SQL is authored, not a model submission. All counterfactual observations are synthetic. No candidate SQL is executed locally. Native execution, equivalent-method checks and hostile controls run separately in hosted Actions.

Independent source-first review verified source response and extract hashes, all original Decimal gold and nine control expected values. Review corrected equivalent revenue and consolidated segment-total support paths, Oracle adjusted-value locators and inapplicable timestamp caveats before exposure. It is not a claim of human review.
