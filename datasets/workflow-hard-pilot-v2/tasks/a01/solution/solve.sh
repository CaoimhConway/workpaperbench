#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/proposal_tests.sql <<'SQL'
WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , proposed AS (
 SELECT q.*,v.*,MAX(0.0,(special_dividend-b)/(1-r)) draw FROM q CROSS JOIN proposals v
), tested AS (
 SELECT *, (ebitda-net_cash_capex)/(fixed_charges+r*draw+special_dividend) ratio FROM proposed
)
SELECT scenario,proposal,draw required_draw_usd_million,
 covenant_availability-draw covenant_availability_usd_million,ratio fixed_charge_ratio,
 CASE WHEN draw>=trigger_draw THEN 1 ELSE 0 END covenant_tested,
 CASE WHEN draw<=capacity AND (draw<trigger_draw OR ratio>=1) THEN 1 ELSE 0 END feasible FROM tested
SQL
cat > /logs/artifacts/distribution_frontier.sql <<'SQL'
WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , vertices AS (
 SELECT scenario,trigger_draw d FROM q WHERE capacity>=trigger_draw
 UNION SELECT scenario,capacity FROM q WHERE capacity>=trigger_draw
 UNION SELECT scenario,MAX(trigger_draw,MIN(capacity,h-b)) FROM q WHERE capacity>=trigger_draw
), options AS (
 SELECT scenario,b+(1-r)*MIN(capacity,trigger_draw) value,
 CASE WHEN capacity<trigger_draw THEN 1 ELSE 0 END attained FROM q
 UNION ALL
 SELECT q.scenario,MIN(b+(1-r)*d,h-r*d),1 FROM q JOIN vertices USING(scenario)
 WHERE MIN(b+(1-r)*d,h-r*d)>=0
), best AS (SELECT scenario,MAX(value) value FROM options GROUP BY scenario)
SELECT b.scenario,b.value upper_limit_usd_million,MAX(o.attained) attainable
 FROM best b JOIN options o ON b.scenario=o.scenario AND ABS(b.value-o.value)<1e-9
 GROUP BY b.scenario,b.value
SQL
cat > /logs/artifacts/equity_support.sql <<'SQL'
WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) , required AS (
 SELECT q.*,v.*,MIN(capacity,(h-special_dividend)/r) active_draw,
 special_dividend-b-(1-r)*MIN(capacity,trigger_draw) gap FROM q CROSS JOIN equity_targets v
), options AS (
 SELECT scenario,target,MAX(0.0,gap) value,
 CASE WHEN capacity<trigger_draw OR gap<0 THEN 1 ELSE 0 END attained FROM required
 UNION ALL SELECT scenario,target,MAX(0.0,special_dividend-b-(1-r)*active_draw),1
 FROM required WHERE active_draw>=trigger_draw
), best AS (SELECT scenario,target,MIN(value) value FROM options GROUP BY scenario,target)
SELECT b.scenario,b.target,b.value lower_limit_usd_million,MAX(o.attained) attainable
 FROM best b JOIN options o ON b.scenario=o.scenario AND b.target=o.target AND ABS(b.value-o.value)<1e-9
 GROUP BY b.scenario,b.target,b.value
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-pilot-v2-a01",
  "tables": [
    {
      "id": "proposal_tests",
      "file": "proposal_tests.sql",
      "evidence": [
        "a01:s01",
        "a01:s02",
        "a01:s04"
      ]
    },
    {
      "id": "distribution_frontier",
      "file": "distribution_frontier.sql",
      "evidence": [
        "a01:s01",
        "a01:s02",
        "a01:s04"
      ]
    },
    {
      "id": "equity_support",
      "file": "equity_support.sql",
      "evidence": [
        "a01:s01",
        "a01:s02",
        "a01:s04"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "contradicted",
      "evidence": [
        "a01:s01",
        "a01:s04"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "supported",
      "evidence": [
        "a01:s01",
        "a01:s02",
        "a01:s04"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "a01:s01",
        "a01:s02"
      ]
    }
  ]
}
ANSWER
