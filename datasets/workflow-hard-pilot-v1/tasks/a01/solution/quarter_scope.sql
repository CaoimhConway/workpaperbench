WITH q AS (
 SELECT c.segment,c.ifrs+c.divestments+c.calendar current_q4,
 p.fy2016,p.fy2015,p.q42015,m.q42015_matched,
 p.q42015-m.q42015_matched extra_week
 FROM quarter_current c JOIN period_sales p USING(segment) JOIN matched_quarter m USING(segment)
) SELECT segment,current_q4 proforma_q42016_eur_million,
 extra_week extra_week2015_eur_million,current_q4-q42015_matched change_eur_million,
 100.0*(current_q4/q42015_matched-1) growth_pct FROM q
