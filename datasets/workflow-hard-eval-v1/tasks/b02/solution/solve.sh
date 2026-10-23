#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/sale_allocations.sql <<'SQL'
WITH terms_full AS (
 SELECT p.*,t.issue_price,t.preference_multiple,t.conversion_ratio,t.rank,t.forced_eligible,
 p.shares*t.issue_price*t.preference_multiple/1000000.0 preference,
 p.shares*t.conversion_ratio/1000000.0 converted
 FROM preferred p JOIN terms t USING(series)
), common_count AS (SELECT SUM(shares)/1000000.0 shares FROM common)
, cases AS (
 SELECT s.*,s.proceeds>t.valuation forced FROM sale_cases s CROSS JOIN trigger t
), remaining AS (
 SELECT c.sale_case,c.proceeds,n.* FROM cases c CROSS JOIN terms_full n
 WHERE NOT(c.forced=1 AND n.forced_eligible=1)
), totals AS (
 SELECT c.*,b.shares+COALESCE((SELECT SUM(n.converted) FROM terms_full n
 WHERE c.forced=1 AND n.forced_eligible=1),0) base,
 COALESCE((SELECT SUM(preference) FROM remaining r WHERE r.sale_case=c.sale_case),0) preference_total
 FROM cases c CROSS JOIN common_count b
), prefixes AS (
 SELECT r.*,SUM(preference) OVER(PARTITION BY sale_case ORDER BY preference/converted,series
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) removed,
 SUM(converted) OVER(PARTITION BY sale_case ORDER BY preference/converted,series
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) added
 FROM remaining r
), prices AS (
 SELECT sale_case,MAX(0.0,MIN(price)) price FROM (
 SELECT sale_case,(proceeds-preference_total)/base price FROM totals
 UNION ALL SELECT p.sale_case,(t.proceeds-t.preference_total+p.removed)/(t.base+p.added)
 FROM prefixes p JOIN totals t USING(sale_case)
 ) GROUP BY sale_case
), payments AS (
 SELECT c.sale_case,n.series security,n.shares,
 CASE WHEN c.forced=1 AND n.forced_eligible=1 THEN n.converted*p.price
 WHEN c.proceeds>=t.preference_total THEN MAX(n.preference,n.converted*p.price)
 ELSE MIN(n.preference,MAX(0.0,c.proceeds-COALESCE((SELECT SUM(r.preference)
 FROM remaining r WHERE r.sale_case=c.sale_case AND r.rank<n.rank),0))*n.preference/
 (SELECT SUM(r.preference) FROM remaining r WHERE r.sale_case=c.sale_case AND r.rank=n.rank)) END cash
 FROM cases c CROSS JOIN terms_full n JOIN prices p USING(sale_case) JOIN totals t USING(sale_case)
 UNION ALL SELECT p.sale_case,c.security,c.shares,c.shares/1000000.0*p.price FROM prices p CROSS JOIN common c
) SELECT sale_case,security,cash cash_usd_million,cash*1000000.0/shares payout_per_share FROM payments
SQL
cat > /logs/artifacts/conversion_frontiers.sql <<'SQL'
WITH terms_full AS (
 SELECT p.*,t.issue_price,t.preference_multiple,t.conversion_ratio,t.rank,t.forced_eligible,
 p.shares*t.issue_price*t.preference_multiple/1000000.0 preference,
 p.shares*t.conversion_ratio/1000000.0 converted
 FROM preferred p JOIN terms t USING(series)
), common_count AS (SELECT SUM(shares)/1000000.0 shares FROM common)
, modes(forced) AS (SELECT 0 UNION ALL SELECT 1), branch_totals AS (
 SELECT m.forced,b.shares+SUM(CASE WHEN m.forced=1 AND t.forced_eligible=1
 THEN t.converted ELSE 0.0 END) base FROM modes m CROSS JOIN common_count b CROSS JOIN terms_full t
 GROUP BY m.forced,b.shares
), remaining AS (
 SELECT m.forced,t.* FROM modes m CROSS JOIN terms_full t WHERE NOT(m.forced=1 AND t.forced_eligible=1)
)
, candidates AS (
 SELECT n.series,b.forced,n.preference/n.converted price,
 b.base*n.preference/n.converted+SUM(MAX(r.preference,r.converted*n.preference/n.converted)) proceeds
 FROM terms_full n CROSS JOIN branch_totals b JOIN remaining r ON r.forced=b.forced
 WHERE n.forced_eligible=0 GROUP BY n.series,b.forced,n.preference,n.converted,b.base
) SELECT c.series,MIN(c.proceeds) proceeds_usd_million,c.price common_payout_per_share
 FROM candidates c CROSS JOIN trigger t WHERE (c.proceeds>t.valuation)=c.forced
 GROUP BY c.series,c.price
SQL
cat > /logs/artifacts/owner_funding.sql <<'SQL'
WITH terms_full AS (
 SELECT p.*,t.issue_price,t.preference_multiple,t.conversion_ratio,t.rank,t.forced_eligible,
 p.shares*t.issue_price*t.preference_multiple/1000000.0 preference,
 p.shares*t.conversion_ratio/1000000.0 converted
 FROM preferred p JOIN terms t USING(series)
), common_count AS (SELECT SUM(shares)/1000000.0 shares FROM common)
, modes(forced) AS (SELECT 0 UNION ALL SELECT 1), branch_totals AS (
 SELECT m.forced,b.shares+SUM(CASE WHEN m.forced=1 AND t.forced_eligible=1
 THEN t.converted ELSE 0.0 END) base FROM modes m CROSS JOIN common_count b CROSS JOIN terms_full t
 GROUP BY m.forced,b.shares
), remaining AS (
 SELECT m.forced,t.* FROM modes m CROSS JOIN terms_full t WHERE NOT(m.forced=1 AND t.forced_eligible=1)
)
, owners AS (
 SELECT series security,converted quantity FROM terms_full
 UNION ALL SELECT security,shares/1000000.0 FROM common
), candidates AS (
 SELECT q.target_case,b.forced,
 CASE WHEN h.series IS NOT NULL AND q.cash_target<=h.preference THEN
 COALESCE((SELECT SUM(r.preference) FROM remaining r WHERE r.forced=b.forced AND r.rank<h.rank),0)
 +q.cash_target/h.preference*(SELECT SUM(r.preference) FROM remaining r WHERE r.forced=b.forced AND r.rank=h.rank)
 ELSE b.base*q.cash_target/o.quantity+(SELECT SUM(MAX(r.preference,r.converted*q.cash_target/o.quantity))
 FROM remaining r WHERE r.forced=b.forced) END required
 FROM owner_targets q JOIN owners o USING(security) CROSS JOIN branch_totals b
 LEFT JOIN remaining h ON h.forced=b.forced AND h.series=q.security
), feasible AS (
 SELECT c.target_case,CASE WHEN forced=1 THEN MAX(required,t.valuation) ELSE required END value,
 CASE WHEN forced=0 OR required>t.valuation THEN 1 ELSE 0 END attained
 FROM candidates c CROSS JOIN trigger t WHERE forced=1 OR required<=t.valuation
), minima AS (SELECT target_case,MIN(value) value FROM feasible GROUP BY target_case)
 SELECT m.target_case,m.value proceeds_infimum_usd_million,MAX(f.attained) attained
 FROM minima m JOIN feasible f ON f.target_case=m.target_case AND f.value=m.value
 GROUP BY m.target_case,m.value
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-eval-v1-b02",
  "tables": [
    {
      "id": "sale_allocations",
      "file": "sale_allocations.sql",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s03",
        "b02:s05"
      ]
    },
    {
      "id": "conversion_frontiers",
      "file": "conversion_frontiers.sql",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s03",
        "b02:s05"
      ]
    },
    {
      "id": "owner_funding",
      "file": "owner_funding.sql",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s03",
        "b02:s05"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s03",
        "b02:s05"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "b02:s01",
        "b02:s02",
        "b02:s03",
        "b02:s05"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "b02:s05",
        "b02:s06"
      ]
    }
  ]
}
ANSWER
