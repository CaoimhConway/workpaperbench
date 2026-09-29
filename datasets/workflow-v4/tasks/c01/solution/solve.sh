#!/bin/bash
set -euo pipefail
cat > /logs/artifacts/revenue_bridge.sql <<'SQL'
WITH p AS (SELECT category,
 MAX(CASE WHEN period_end='2023-12-31' THEN amount END) prior,
 MAX(CASE WHEN period_end='2024-12-31' THEN amount END) current
 FROM revenues WHERE months=12 AND period_end IN ('2023-12-31','2024-12-31') GROUP BY category),
t AS (SELECT prior,current FROM p WHERE category='Total net revenue')
SELECT CASE p.category WHEN 'Transaction-based revenue' THEN 'transaction' WHEN 'Subscription and services-based revenue'
THEN 'subscription' WHEN 'Hardware revenue' THEN 'hardware' ELSE 'bitcoin' END category,
p.prior revenue_2023_usd_thousand,p.current revenue_2024_usd_thousand,p.current-p.prior change_usd_thousand,
100.0*(p.current-p.prior)/(t.current-t.prior) contribution_pct,
100.0*p.prior/t.prior share_2023_pct,100.0*p.current/t.current share_2024_pct,
100.0*p.current/t.current-100.0*p.prior/t.prior share_change_pp
FROM p CROSS JOIN t WHERE p.category!='Total net revenue'
SQL
cat > /logs/artifacts/profit_bridge.sql <<'SQL'
WITH components AS (
 SELECT period_end,replace(category,' revenue','') name,amount signed_amount FROM revenues
 WHERE months=12 AND category!='Total net revenue'
 UNION ALL SELECT period_end,replace(category,' costs',''),-amount FROM costs WHERE months=12 AND category!='Total cost of revenue'),
p AS (SELECT name,SUM(CASE WHEN period_end='2023-12-31' THEN signed_amount ELSE 0 END) prior,
SUM(CASE WHEN period_end='2024-12-31' THEN signed_amount ELSE 0 END) current FROM components
WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY name)
SELECT CASE name WHEN 'Transaction-based' THEN 'transaction' WHEN 'Subscription and services-based' THEN 'subscription'
WHEN 'Hardware' THEN 'hardware' WHEN 'Bitcoin' THEN 'bitcoin' ELSE 'acquired_technology_amortization' END category,
prior gross_profit_2023_usd_thousand,current gross_profit_2024_usd_thousand,current-prior change_usd_thousand FROM p
SQL
cat > /logs/artifacts/reconciliation.sql <<'SQL'
WITH totals AS (
 SELECT period_end,amount revenue FROM revenues WHERE months=12 AND category='Total net revenue'),
 c AS (SELECT period_end,amount cost FROM costs WHERE months=12 AND category='Total cost of revenue'),
 r AS (SELECT period_end,SUM(amount) amount FROM revenues WHERE months=12 AND category!='Total net revenue' GROUP BY period_end),
 s AS (SELECT period_end,SUM(amount) amount FROM costs WHERE months=12 AND category!='Total cost of revenue' GROUP BY period_end),
 b AS (SELECT v.period_end,v.amount-k.amount gp FROM revenues v JOIN costs k ON v.period_end=k.period_end
AND v.months=k.months WHERE v.months=12 AND v.category='Bitcoin revenue' AND k.category='Bitcoin costs'),
 p AS (SELECT t.period_end,t.revenue,c.cost,r.amount component_revenue,s.amount component_cost,b.gp
 FROM totals t JOIN c USING(period_end) JOIN r USING(period_end) JOIN s USING(period_end) JOIN b USING(period_end))
SELECT n.revenue-o.revenue revenue_change_usd_thousand,(n.revenue-n.cost)-(o.revenue-o.cost) gross_profit_change_usd_thousand,
(n.revenue-o.revenue)-(n.component_revenue-o.component_revenue) revenue_residual_usd_thousand,
((n.revenue-n.cost)-(o.revenue-o.cost))-((n.component_revenue-n.component_cost)-(o.component_revenue-o.component_cost)) gross_profit_residual_usd_thousand,
100.0*(n.gp/o.gp-1) bitcoin_gross_profit_growth_pct FROM p n CROSS JOIN p o WHERE n.period_end='2024-12-31' AND o.period_end='2023-12-31'
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-v4-c01",
  "tables": [
    {
      "id": "revenue_bridge",
      "file": "revenue_bridge.sql",
      "evidence": [
        "c03:s01"
      ]
    },
    {
      "id": "profit_bridge",
      "file": "profit_bridge.sql",
      "evidence": [
        "c03:s01",
        "c03:s02"
      ]
    },
    {
      "id": "reconciliation",
      "file": "reconciliation.sql",
      "evidence": [
        "c03:s01",
        "c03:s02"
      ]
    }
  ],
  "claims": [
    {
      "id": "bitcoin_majority_of_total_revenue_increase",
      "verdict": "contradicted",
      "evidence": [
        "c03:s01"
      ]
    },
    {
      "id": "all_components_reconcile",
      "verdict": "supported",
      "evidence": [
        "c03:s01",
        "c03:s02"
      ]
    },
    {
      "id": "bitcoin_price_effect_identifiable",
      "verdict": "unresolved",
      "evidence": [
        "c03:s03"
      ]
    }
  ]
}
ANSWER
