WITH p AS (SELECT period,
MAX(CASE WHEN measure='gaap' THEN amount_usd_thousand END) g,
SUM(CASE WHEN group_name='prior_adjustment' THEN amount_usd_thousand ELSE 0 END) a,
SUM(CASE WHEN group_name='extra_adjustment' THEN amount_usd_thousand ELSE 0 END) e,
MAX(CASE WHEN measure='prior_definition' THEN amount_usd_thousand END) old,
MAX(CASE WHEN measure='new_definition' THEN amount_usd_thousand END) new
FROM expense_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025') GROUP BY period),
all_periods AS (SELECT * FROM p UNION ALL SELECT '9M'||a.period,a.g-q.g,a.a-q.a,a.e-q.e,a.old-q.old,a.new-q.new
FROM p a JOIN p q ON q.period='Q4'||a.period WHERE a.period IN ('FY2024','FY2025'))
SELECT period,g gaap_expense_usd_thousand,g+a prior_adjusted_usd_thousand,g+a new_adjusted_usd_thousand,
-e additional_exclusions_usd_thousand,g+a-old prior_residual_usd_thousand,g+a+e-new new_residual_usd_thousand FROM all_periods
