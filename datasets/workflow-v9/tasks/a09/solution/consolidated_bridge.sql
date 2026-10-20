WITH p AS (SELECT * FROM segments WHERE fiscal_year IN (2024,2025)),periods AS (SELECT * FROM p UNION ALL
SELECT a.fiscal_year,9,a.segment,a.revenue_usd_million-q.revenue_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment AND a.months=12 AND q.months=3) ,r AS (SELECT * FROM reconciliation WHERE fiscal_year IN (2024,2025)),recons AS (SELECT * FROM r UNION ALL SELECT a.fiscal_year,9,
a.pretax_income_usd_million-q.pretax_income_usd_million,a.corporate_usd_million-q.corporate_usd_million,a.india_loss_usd_million-q.india_loss_usd_million,
a.restructuring_usd_million-q.restructuring_usd_million,a.other_expense_usd_million-q.other_expense_usd_million,a.interest_usd_million-q.interest_usd_million,
a.amortization_usd_million-q.amortization_usd_million,a.reported_segment_operating_usd_million-q.reported_segment_operating_usd_million,
a.revenue_eliminations_usd_million-q.revenue_eliminations_usd_million FROM r a JOIN r q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3)
SELECT p.fiscal_year,p.months,SUM(p.revenue_usd_million) gross_segment_revenue_usd_million,r.revenue_eliminations_usd_million,
SUM(p.revenue_usd_million)+r.revenue_eliminations_usd_million consolidated_revenue_usd_million,SUM(p.operating_income_usd_million) segment_operating_usd_million,
r.pretax_income_usd_million,r.corporate_usd_million+r.india_loss_usd_million+r.restructuring_usd_million+r.other_expense_usd_million+r.interest_usd_million+r.amortization_usd_million signed_bridge_usd_million,
r.pretax_income_usd_million+r.corporate_usd_million+r.india_loss_usd_million+r.restructuring_usd_million+r.other_expense_usd_million+r.interest_usd_million+r.amortization_usd_million-SUM(p.operating_income_usd_million) pretax_bridge_residual_usd_million,
SUM(p.operating_income_usd_million)-r.reported_segment_operating_usd_million segment_sum_residual_usd_million FROM periods p JOIN recons r USING(fiscal_year,months) GROUP BY p.fiscal_year,p.months
