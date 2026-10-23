WITH l AS (SELECT c.gross-p.gross gross,c.accumulated-p.accumulated accumulated,(c.gross-p.gross)-(c.accumulated-p.accumulated) net,
 a.finance_rou_additions additions,a.finance_amortization amort FROM finance_leases c JOIN finance_leases p ON p.year=c.year-1
 JOIN annual_expenses a ON a.year=c.year), bridge AS (
 SELECT 'gross' measure,gross observed,additions explained FROM l UNION ALL
 SELECT 'accumulated',accumulated,amort FROM l UNION ALL SELECT 'net',net,additions-amort FROM l)
 SELECT measure,observed change_usd_million,explained explained_change_usd_million,observed-explained residual_usd_million FROM bridge
