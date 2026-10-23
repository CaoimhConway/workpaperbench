#!/bin/bash
set -euo pipefail
mkdir -p /logs/artifacts
cat > /logs/artifacts/quarter_scope.sql <<'SQL'
WITH q AS (
 SELECT c.segment,c.ifrs+c.divestments+c.calendar current_q4,
 p.fy2016,p.fy2015,p.q42015,m.q42015_matched,
 p.q42015-m.q42015_matched extra_week
 FROM quarter_current c JOIN period_sales p USING(segment) JOIN matched_quarter m USING(segment)
) SELECT segment,current_q4 proforma_q42016_eur_million,
 extra_week extra_week2015_eur_million,current_q4-q42015_matched change_eur_million,
 100.0*(current_q4/q42015_matched-1) growth_pct FROM q
SQL
cat > /logs/artifacts/comparable_periods.sql <<'SQL'
WITH q AS (
 SELECT c.segment,c.ifrs+c.divestments+c.calendar current_q4,
 p.fy2016,p.fy2015,p.q42015,m.q42015_matched,
 p.q42015-m.q42015_matched extra_week
 FROM quarter_current c JOIN period_sales p USING(segment) JOIN matched_quarter m USING(segment)
) , periods AS (
 SELECT segment,'fy' period,fy2016 current,fy2015-extra_week prior FROM q
 UNION ALL SELECT segment,'q4',current_q4,q42015_matched FROM q
 UNION ALL SELECT segment,'pre_q4',fy2016-current_q4,fy2015-extra_week-q42015_matched FROM q
) SELECT segment,period,current current_eur_million,prior prior_eur_million,
 current-prior change_eur_million,100.0*(current/prior-1) growth_pct FROM periods
SQL
cat > /logs/artifacts/annual_change_bridge.sql <<'SQL'
WITH q AS (
 SELECT c.segment,c.ifrs+c.divestments+c.calendar current_q4,
 p.fy2016,p.fy2015,p.q42015,m.q42015_matched,
 p.q42015-m.q42015_matched extra_week
 FROM quarter_current c JOIN period_sales p USING(segment) JOIN matched_quarter m USING(segment)
) , g AS (
 SELECT MAX(CASE WHEN year=2016 THEN ifrs END) i1,MAX(CASE WHEN year=2015 THEN ifrs END) i0,
 MAX(CASE WHEN year=2016 THEN proforma END) p1,MAX(CASE WHEN year=2015 THEN proforma END) p0 FROM group_annual
), s AS (SELECT SUM(extra_week) w,SUM(fy2016-fy2015+extra_week) delta FROM q)
 SELECT i1-i0 statutory_change_eur_million,(p1-i1)-(p0-i0) presentation_change_eur_million,
 w prior_extra_week_eur_million,p1-p0+w comparable_change_eur_million,
 100.0*(p1-p0+w)/(p0-w) comparable_growth_pct,delta-(p1-p0+w) segment_residual_eur_million FROM g CROSS JOIN s
SQL
cat > /logs/artifacts/answer.json <<'ANSWER'
{
  "task_id": "workflow-hard-pilot-v1-a01",
  "tables": [
    {
      "id": "quarter_scope",
      "file": "quarter_scope.sql",
      "evidence": [
        "a01:s02",
        "a01:s03",
        "a01:s04"
      ]
    },
    {
      "id": "comparable_periods",
      "file": "comparable_periods.sql",
      "evidence": [
        "a01:s02",
        "a01:s03",
        "a01:s04"
      ]
    },
    {
      "id": "annual_change_bridge",
      "file": "annual_change_bridge.sql",
      "evidence": [
        "a01:s03",
        "a01:s04",
        "a01:s05"
      ]
    }
  ],
  "claims": [
    {
      "id": "claim_1",
      "verdict": "supported",
      "evidence": [
        "a01:s02",
        "a01:s03"
      ]
    },
    {
      "id": "claim_2",
      "verdict": "contradicted",
      "evidence": [
        "a01:s03",
        "a01:s04",
        "a01:s05"
      ]
    },
    {
      "id": "claim_3",
      "verdict": "unresolved",
      "evidence": [
        "a01:s01",
        "a01:s03",
        "a01:s04"
      ]
    }
  ]
}
ANSWER
