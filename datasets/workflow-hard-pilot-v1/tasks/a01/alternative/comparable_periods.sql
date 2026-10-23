WITH q AS (
 SELECT c.segment,c.ifrs+c.divestments+c.calendar current_q4,
 p.fy2016,p.fy2015,p.q42015,m.q42015_matched,
 p.q42015-m.q42015_matched extra_week
 FROM quarter_current c JOIN period_sales p USING(segment) JOIN matched_quarter m USING(segment)
) , periods AS (
 SELECT segment,'fy' period,fy2016 current,fy2015-extra_week prior FROM q
 UNION ALL SELECT segment,'q4',current_q4,q42015_matched FROM q
 UNION ALL SELECT segment,'pre_q4',fy2016-current_q4,fy2015-q42015 FROM q
) SELECT segment,period,current current_eur_million,prior prior_eur_million,
 current-prior change_eur_million,100.0*(current/prior-1) growth_pct FROM periods
