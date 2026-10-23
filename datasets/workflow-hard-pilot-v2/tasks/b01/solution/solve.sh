#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/settlement_scenarios.sql <<'SQL'
WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) SELECT p.price_case,n.note,
 CASE WHEN principal_settlement='cash' OR full_shares*p.price<=principal
 THEN principal ELSE 0.0 END cash_usd_million,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)
 WHEN full_shares*p.price>principal THEN full_shares ELSE 0.0 END gross_shares_million
 FROM instruments n CROSS JOIN price_cases p
SQL
cat > /logs/artifacts/diluted_eps.sql <<'SQL'
WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) , components AS (
 SELECT p.price_case,n.note,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)
 ELSE full_shares END shares,
 CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment,
 ROW_NUMBER() OVER(PARTITION BY p.price_case ORDER BY n.note) position
 FROM instruments n CROSS JOIN price_cases p
) , masks(mask) AS (
 SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
), candidates AS (
 SELECT c.price_case,i.income_case,i.income,b.basic_shares,m.mask,
 i.income+SUM(CASE WHEN (m.mask & (1 << (c.position-1)))!=0 THEN adjustment ELSE 0 END) numerator,
 b.basic_shares+b.award_shares+
 SUM(CASE WHEN (m.mask & (1 << (c.position-1)))!=0 THEN shares ELSE 0 END) denominator
 FROM components c CROSS JOIN income_cases i CROSS JOIN eps_basis b CROSS JOIN masks m
 GROUP BY c.price_case,i.income_case,i.income,b.basic_shares,b.award_shares,m.mask
) SELECT price_case,income_case,income/basic_shares basic_eps,
 MIN(numerator/denominator) diluted_eps FROM candidates
 GROUP BY price_case,income_case,income,basic_shares
SQL
cat > /logs/artifacts/thresholds.sql <<'SQL'
WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) , components AS (
 SELECT note,principal_settlement,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/q.price)
 ELSE full_shares END shares,
 CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment
 FROM instruments CROSS JOIN threshold_case q
), boundaries AS (
 SELECT c.note,c.adjustment/c.shares*(b.basic_shares+b.award_shares+
 COALESCE(SUM(o.shares),0))-COALESCE(SUM(o.adjustment),0) value
 FROM components c CROSS JOIN eps_basis b LEFT JOIN components o
 ON o.shares>0 AND o.adjustment*c.shares<c.adjustment*o.shares
 WHERE c.principal_settlement!='cash'
 GROUP BY c.note,c.adjustment,c.shares,b.basic_shares,b.award_shares
) SELECT 'earnings_'||note measure,value FROM boundaries UNION ALL
 SELECT 'share_price',SUM(CASE WHEN principal_settlement='cash' THEN principal ELSE 0 END)
 /(SUM(full_shares)-q.target_shares) FROM instruments CROSS JOIN threshold_case q
 GROUP BY q.target_shares
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-pilot-v2-b01",
  "tables": [
    {
      "id": "settlement_scenarios",
      "file": "settlement_scenarios.sql",
      "evidence": [
        "b01:s01",
        "b01:s03",
        "b01:s04",
        "b01:s05",
        "b01:s08"
      ]
    },
    {
      "id": "diluted_eps",
      "file": "diluted_eps.sql",
      "evidence": [
        "b01:s01",
        "b01:s03",
        "b01:s04",
        "b01:s05",
        "b01:s08",
        "b01:s02",
        "b01:s06",
        "b01:s07"
      ]
    },
    {
      "id": "thresholds",
      "file": "thresholds.sql",
      "evidence": [
        "b01:s01",
        "b01:s03",
        "b01:s04",
        "b01:s05",
        "b01:s08",
        "b01:s02",
        "b01:s06",
        "b01:s07"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "b01:s01",
        "b01:s03",
        "b01:s04",
        "b01:s05",
        "b01:s08",
        "b01:s02",
        "b01:s06",
        "b01:s07"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "b01:s05"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "b01:s06",
        "b01:s08"
      ]
    }
  ]
}
ANSWER
