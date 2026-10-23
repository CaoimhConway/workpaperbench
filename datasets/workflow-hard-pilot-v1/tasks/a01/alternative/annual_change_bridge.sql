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
