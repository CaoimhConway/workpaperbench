# Private authoring note

Decision: compare realized Q4 execution with guidance that preceded it and separate operating adjustments from EPS. Required selections: prior issued Q4 non-GAAP range, actual Q4 rather than FY/Q3, signed operating bridge rather than net-income adjustments. Independent source-table parsing checked the retained values against accession-specific HTML before calculating with Decimal.

Candidate-only audit: question/contract contains no quantities or verdict hints. Disclosed adjusted income alone cannot answer the EPS comparison, margin denominator and GAAP bridge. Copying the adjusted subtotal is intentionally insufficient for the signed component control. Future targets, annual columns and nearby quarters remain source-faithful alternatives. Blanket refusal cannot pass. Wrong approaches include using subsequent targets, annual margins, adding all EPS adjustments to operating income, or dropping signed reversals. Accepted evidence paths include the reconciliation containing GAAP income itself. No human review is claimed.

Independent Decimal results from factual rows:

{
  "eps_difference": "0.13",
  "adjusted_operating_income": "2596.0",
  "adjusted_margin": "46.30752764894755618979664645",
  "margin_bridge": "1139.850160542276132714948270"
}

Controls are synthetic. Expected changed quantities are computed by the same documented financial definitions over independently altered inputs, without executing submitted SQL.

The EPS-observation control changes actual EPS to 4.91 and prior upper guidance to 4.72, independently giving 0.19 USD per share. The signed bridge leaves reported adjusted income at 2,596 while its components rebuild to 2,621. This intentionally unreconciled reported comparison detects copying. All candidate source rows, including the loss-contingency and lease adjustment, are retained.
