WITH components AS (SELECT measure,
-MAX(CASE WHEN period='FY2024' THEN amount_usd_thousand END) p,
-MAX(CASE WHEN period='FY2025' THEN amount_usd_thousand END) c FROM expense_reconciliation
WHERE group_name='extra_adjustment' AND period IN ('FY2024','FY2025') GROUP BY measure),
delta AS (SELECT SUM(c-p) total FROM components)
SELECT measure,p prior_usd_thousand,c current_usd_thousand,c-p change_usd_thousand,
100.0*(c-p)/total contribution_to_definition_gap_change_pct FROM components CROSS JOIN delta
