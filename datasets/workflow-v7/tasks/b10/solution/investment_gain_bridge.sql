WITH p AS (SELECT year,SUM(CASE WHEN measure='equity_unrealized' THEN pretax_gain_usd_million ELSE 0 END) unrealized,
SUM(CASE WHEN measure='equity_sold' THEN pretax_gain_usd_million ELSE 0 END) sold,
SUM(CASE WHEN measure IN ('fixed_realized_gain','fixed_realized_loss') THEN pretax_gain_usd_million ELSE 0 END) fixed,
SUM(CASE WHEN measure='other' THEN pretax_gain_usd_million ELSE 0 END) other,SUM(pretax_gain_usd_million) total FROM investment_components GROUP BY year)
SELECT p.year,p.unrealized unrealized_equity_gain_usd_million,p.sold equity_sold_gain_usd_million,p.fixed fixed_net_gain_usd_million,p.other other_gain_usd_million,
p.total pretax_gain_usd_million,p.total+c.signed_cash_adjustment_usd_million cash_removal_residual_usd_million,
100.0*p.unrealized/p.total unrealized_to_net_gain_pct FROM p JOIN cash_adjustments c ON p.year=c.year AND c.measure='investment_gain' WHERE p.year IN (2023,2024,2025)
