"""Marketplace-specific references, SQL work products and regression checks."""
import copy
from decimal import Decimal
from build_workflow_tasks import TEXT, INTEGER, numeric, table
from workflow_development_cases import claim
D=lambda x:Decimal(str(x))
M=numeric('usd_million',0.001)
P=numeric('percent')
N=numeric('million')
U=numeric('usd')

def uber(data):
    segment=[]
    selected=[r for r in data['segments'] if r['year'] in (2024,2025)]
    platforms={r['year']:r for r in data['platform'] if r['year'] in (2024,2025)}
    for r in selected:
        b,v,e=[D(r[k]) for k in ('bookings_usd_million','revenue_usd_million','adjusted_ebitda_usd_million')]
        segment.append([r['year'],r['segment'],float(b),float(v),float(e),float(100*v/b),float(100*e/b)])
    corporate=[]
    usage=[]
    for year,p in platforms.items():
        rows=[r for r in selected if r['year']==year]
        b,v,e=[sum((D(r[k]) for r in rows),D(0)) for k in ('bookings_usd_million','revenue_usd_million','adjusted_ebitda_usd_million')]
        c=D(p['corporate_cost_usd_million'])
        corporate.append([year,float(e),float(c),float(e+c),float(e+c-D(p['adjusted_ebitda_usd_million'])),float(b-D(p['bookings_usd_million'])),float(v-D(p['revenue_usd_million'])),float(100*(e+c)/b)])
        trips,consumers=D(p['trips_million']),D(p['mapcs_million'])
        usage.append([year,p['months'],float(trips),float(consumers),float(trips/consumers),float(trips/consumers/D(p['months']))])
    return {'segment_metrics':segment,'corporate_bridge':corporate,'consumer_activity':usage}

UBER_SEGMENT="""SELECT CAST(year AS INTEGER) year,segment,bookings_usd_million,revenue_usd_million,adjusted_ebitda_usd_million,
100.0*revenue_usd_million/bookings_usd_million revenue_to_bookings_pct,
100.0*adjusted_ebitda_usd_million/bookings_usd_million ebitda_to_bookings_pct FROM segments WHERE year IN (2024,2025)"""
UBER_CORPORATE="""WITH s AS (SELECT year,SUM(bookings_usd_million) b,SUM(revenue_usd_million) r,SUM(adjusted_ebitda_usd_million) e FROM segments GROUP BY year)
SELECT CAST(p.year AS INTEGER) year,e segment_sum_usd_million,p.corporate_cost_usd_million,e+p.corporate_cost_usd_million total_adjusted_ebitda_usd_million,
e+p.corporate_cost_usd_million-p.adjusted_ebitda_usd_million ebitda_residual_usd_million,
b-p.bookings_usd_million bookings_residual_usd_million,r-p.revenue_usd_million revenue_residual_usd_million,
100.0*(e+p.corporate_cost_usd_million)/b total_ebitda_to_bookings_pct FROM platform p JOIN s ON p.year=s.year WHERE p.year IN (2024,2025)"""
UBER_USAGE="""SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,trips_million,mapcs_million,
1.0*trips_million/mapcs_million quarterly_trips_per_monthly_consumer,
1.0*trips_million/mapcs_million/months monthly_trips_per_monthly_consumer FROM platform WHERE year IN (2024,2025)"""

def airbnb(data):
    rows=[r for r in data['quarters'] if r['year'] in (2024,2025)]
    index={(r['year'],r['quarter']):r for r in rows}
    bookings=[]
    cash=[]
    for r in rows:
        v=D(r['gbv_usd_billion'])*1000
        units=D(r['nights_and_seats_million'])
        revenue=D(r['revenue_usd_million'])
        adr=v/units
        bookings.append([r['year'],r['quarter'],float(v),float(units),float(adr),float(adr-D(r['reported_adr_usd'])),float(100*revenue/v)])
        fcf=D(r['operating_cash_usd_million'])-D(r['capex_usd_million'])
        cash.append([r['year'],r['quarter'],float(fcf),float(100*fcf/revenue),float(100*D(r['adjusted_ebitda_usd_million'])/revenue)])
    rolling=[]
    for r in data['rolling_disclosures']:
        if r['year']!=2025:continue
        q=r['quarter']
        window=[index[2024,k] for k in range(q+1,5)]+[index[2025,k] for k in range(1,q+1)]
        rev=sum((D(x['revenue_usd_million']) for x in window),D(0))
        fcf=sum((D(x['operating_cash_usd_million'])-D(x['capex_usd_million']) for x in window),D(0))
        rolling.append([2025,q,float(rev),float(fcf),float(100*fcf/rev),float(rev-D(r['reported_ttm_revenue_usd_million'])),float(fcf-D(r['reported_ttm_fcf_usd_million']))])
    return {'booking_ratios':bookings,'quarter_cash':cash,'rolling_cash':rolling}

AIRBNB_BOOKINGS="""SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,1000.0*gbv_usd_billion gbv_usd_million,nights_and_seats_million,
1000.0*gbv_usd_billion/nights_and_seats_million rounded_input_adr_usd,
1000.0*gbv_usd_billion/nights_and_seats_million-reported_adr_usd adr_rounding_residual_usd,
revenue_usd_million/(10.0*gbv_usd_billion) implied_revenue_to_gbv_pct FROM quarters WHERE year IN (2024,2025)"""
AIRBNB_CASH="""SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,operating_cash_usd_million-capex_usd_million fcf_usd_million,
100.0*(operating_cash_usd_million-capex_usd_million)/revenue_usd_million fcf_margin_pct,
100.0*adjusted_ebitda_usd_million/revenue_usd_million adjusted_ebitda_margin_pct FROM quarters WHERE year IN (2024,2025)"""
AIRBNB_ROLLING="""WITH w AS (SELECT r.year,r.quarter,SUM(q.revenue_usd_million) revenue,SUM(q.operating_cash_usd_million-q.capex_usd_million) fcf,
r.reported_ttm_revenue_usd_million reported_revenue,r.reported_ttm_fcf_usd_million reported_fcf FROM rolling_disclosures r JOIN quarters q
ON q.year*4+q.quarter BETWEEN r.year*4+r.quarter-3 AND r.year*4+r.quarter WHERE r.year=2025 GROUP BY r.year,r.quarter)
SELECT CAST(year AS INTEGER) year,CAST(quarter AS INTEGER) quarter,revenue ttm_revenue_usd_million,fcf ttm_fcf_usd_million,
100.0*fcf/revenue ttm_fcf_margin_pct,revenue-reported_revenue revenue_residual_usd_million,fcf-reported_fcf fcf_residual_usd_million FROM w"""

def shopify(data):
    index={(r['year'],r['months']):r for r in data['periods'] if r['year'] in (2024,2025)}
    components=[]
    cash=[]
    annual={}
    fields=[k for k in next(iter(index.values())) if k not in ('year','months')]
    for year in (2024,2025):
        for months in (3,9,12):
            r={k:D(index[year,12][k])-D(index[year,3][k]) if months==9 else D(index[year,months][k]) for k in fields}
            revenue=r['subscription_revenue_usd_million']+r['merchant_revenue_usd_million']
            sub=r['subscription_revenue_usd_million']-r['subscription_cost_usd_million']
            merchant=r['merchant_revenue_usd_million']-r['merchant_cost_usd_million']
            op=sub+merchant-r['operating_expense_usd_million']
            components.append([year,months,float(sub),float(merchant),float(100*sub/r['subscription_revenue_usd_million']),float(100*merchant/r['merchant_revenue_usd_million']),float(op),float(op-r['reported_operating_income_usd_million']),float(100*r['merchant_revenue_usd_million']/r['gmv_usd_million'])])
            fcf=r['operating_cash_usd_million']-r['capex_usd_million']
            cash.append([year,months,float(revenue),float(fcf),float(100*fcf/revenue),float(fcf-r['reported_fcf_usd_million'])])
            if months==12:annual[year]=r['subscription_revenue_usd_million']
    stocks=[]
    for r in data['subscription_stocks']:
        if r['year'] not in (2024,2025):continue
        stock=D(r['mrr_usd_million'])
        run=12*stock
        stocks.append([r['year'],float(stock),float(run),float(annual[r['year']]),float(run-annual[r['year']]),float(100*(run/annual[r['year']]-1))])
    return {'category_economics':components,'cash_generation':cash,'subscription_stock_bridge':stocks}

SHOPIFY_PERIODS="""WITH periods AS (SELECT * FROM periods WHERE year IN (2024,2025)
UNION ALL SELECT a.year,9,a.gmv_usd_million-q.gmv_usd_million,a.subscription_revenue_usd_million-q.subscription_revenue_usd_million,
a.merchant_revenue_usd_million-q.merchant_revenue_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.merchant_cost_usd_million-q.merchant_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_income_usd_million-q.reported_operating_income_usd_million,a.operating_cash_usd_million-q.operating_cash_usd_million,
a.capex_usd_million-q.capex_usd_million,a.reported_fcf_usd_million-q.reported_fcf_usd_million
FROM periods a JOIN periods q ON a.year=q.year AND a.months=12 AND q.months=3 WHERE a.year IN (2024,2025)) """
# A distinct CTE name avoids shadowing the source table.
SHOPIFY_PERIODS=SHOPIFY_PERIODS.replace('WITH periods AS','WITH p AS')
SHOPIFY_CATEGORY=SHOPIFY_PERIODS+"""SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,
subscription_revenue_usd_million-subscription_cost_usd_million subscription_gp_usd_million,
merchant_revenue_usd_million-merchant_cost_usd_million merchant_gp_usd_million,
100.0*(subscription_revenue_usd_million-subscription_cost_usd_million)/subscription_revenue_usd_million subscription_margin_pct,
100.0*(merchant_revenue_usd_million-merchant_cost_usd_million)/merchant_revenue_usd_million merchant_margin_pct,
subscription_revenue_usd_million+merchant_revenue_usd_million-subscription_cost_usd_million-merchant_cost_usd_million-operating_expense_usd_million operating_income_usd_million,
subscription_revenue_usd_million+merchant_revenue_usd_million-subscription_cost_usd_million-merchant_cost_usd_million-operating_expense_usd_million-reported_operating_income_usd_million residual_usd_million,
100.0*merchant_revenue_usd_million/gmv_usd_million merchant_revenue_to_gmv_pct FROM p"""
SHOPIFY_CASH=SHOPIFY_PERIODS+"""SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,
subscription_revenue_usd_million+merchant_revenue_usd_million revenue_usd_million,operating_cash_usd_million-capex_usd_million fcf_usd_million,
100.0*(operating_cash_usd_million-capex_usd_million)/(subscription_revenue_usd_million+merchant_revenue_usd_million) fcf_margin_pct,
operating_cash_usd_million-capex_usd_million-reported_fcf_usd_million residual_usd_million FROM p"""
SHOPIFY_STOCK="""SELECT CAST(s.year AS INTEGER) year,s.mrr_usd_million,12.0*s.mrr_usd_million exit_annual_run_rate_usd_million,
p.subscription_revenue_usd_million observed_annual_subscription_revenue_usd_million,
12.0*s.mrr_usd_million-p.subscription_revenue_usd_million run_rate_minus_observed_usd_million,
100.0*(12.0*s.mrr_usd_million/p.subscription_revenue_usd_million-1) run_rate_gap_pct
FROM subscription_stocks s JOIN periods p ON s.year=p.year AND p.months=12 WHERE s.year IN (2024,2025)"""

def specifications():
    y={'year':INTEGER}
    q=dict(y,quarter=INTEGER)
    ym=dict(y,months=INTEGER)
    return {
      'b06':{'source':'uber-fy2025','split':'evaluation','calculate':uber,
        'tables':{'segment_metrics':table(dict(y,segment=TEXT,bookings_usd_million=M,revenue_usd_million=M,adjusted_ebitda_usd_million=M,revenue_to_bookings_pct=P,ebitda_to_bookings_pct=P),['year','segment'],[['b06:s01']]),
          'corporate_bridge':table(dict(y,segment_sum_usd_million=M,corporate_cost_usd_million=M,total_adjusted_ebitda_usd_million=M,ebitda_residual_usd_million=M,bookings_residual_usd_million=M,revenue_residual_usd_million=M,total_ebitda_to_bookings_pct=P),['year'],[['b06:s01']]),
          'consumer_activity':table(dict(ym,trips_million=N,mapcs_million=N,quarterly_trips_per_monthly_consumer=numeric('trips'),monthly_trips_per_monthly_consumer=numeric('trips')),['year'],[['b06:s02','b06:s03']])},
        'sql':{'segment_metrics':UBER_SEGMENT,'corporate_bridge':UBER_CORPORATE,'consumer_activity':UBER_USAGE},
        'starting':{'consumer_activity':UBER_USAGE.replace('trips_million/mapcs_million/months','trips_million/mapcs_million')},
        'claims':{'monthly_activity_increased':claim('supported',['b06:s02','b06:s03'],'Monthly trips per monthly active consumer increased between the supplied Q4 periods.'),
          'freight_revenue_is_a_commission':claim('unresolved',['b06:s01','b06:s03'],'Freight revenue divided by bookings uniquely identifies the contractual commission on Freight bookings.'),
          'all_segments_profitable_in_prior_q4':claim('contradicted',['b06:s01'],'Every supplied segment had positive adjusted EBITDA in Q4FY2024.')},
        'request':'Audit the Q4FY2025 platform-metric workpaper against the prior Q4. Preserve segment revenue and booking calculations, reconcile the segment EBITDA sum through corporate costs, and repair the monthly consumer-activity calculation. Report descriptive segment ratios without turning them into contractual commissions.',
        'definitions':{'segment_metrics':'Both years 2024 and 2025. Financial ratios use the matching segment Gross Bookings denominator.',
          'corporate_bridge':'Signed corporate costs plus segment EBITDA equals total EBITDA. Retain booking and revenue reconciliation residuals.',
          'consumer_activity':'Quarterly ratio and monthly ratio are both required. The latter divides quarter trips by the average monthly consumer count and three months.'},
        'rationale':'Monthly averaged audience stocks, quarterly activity flows and heterogeneous booking/revenue presentation interact. Correcting activity duration must preserve negative segment outcomes and the corporate deduction, while an exact fee conclusion stays unidentified.'},
      'b07':{'source':'airbnb-fy2025','split':'evaluation','calculate':airbnb,
        'tables':{'booking_ratios':table(dict(q,gbv_usd_million=M,nights_and_seats_million=N,rounded_input_adr_usd=U,adr_rounding_residual_usd=U,implied_revenue_to_gbv_pct=P),['year','quarter'],[['b07:s01','b07:s02']]),
          'quarter_cash':table(dict(q,fcf_usd_million=M,fcf_margin_pct=P,adjusted_ebitda_margin_pct=P),['year','quarter'],[['b07:s02','b07:s03']]),
          'rolling_cash':table(dict(q,ttm_revenue_usd_million=M,ttm_fcf_usd_million=M,ttm_fcf_margin_pct=P,revenue_residual_usd_million=M,fcf_residual_usd_million=M),['year','quarter'],[['b07:s03']])},
        'sql':{'booking_ratios':AIRBNB_BOOKINGS,'quarter_cash':AIRBNB_CASH,'rolling_cash':AIRBNB_ROLLING},
        'starting':{'rolling_cash':AIRBNB_ROLLING.replace('BETWEEN r.year*4+r.quarter-3 AND r.year*4+r.quarter','= r.year*4+r.quarter').replace('SUM(q.revenue_usd_million)','4*SUM(q.revenue_usd_million)').replace('SUM(q.operating_cash_usd_million-q.capex_usd_million)','4*SUM(q.operating_cash_usd_million-q.capex_usd_million)')},
        'claims':{'ttm_fcf_increased':claim('supported',['b07:s03'],'FY2025 trailing-twelve-month FCF at year end exceeds the same four-quarter measure for FY2024.'),
          'booking_ratio_identifies_fee':claim('unresolved',['b07:s01','b07:s02'],'The implied revenue-to-GBV ratio uniquely identifies the contracted booking fee rate.'),
          'q4_annualization_equals_ttm':claim('contradicted',['b07:s03'],'Four times Q4FY2025 FCF equals the disclosed year-end trailing-twelve-month FCF.')},
        'request':'Audit Airbnb booking and cash-conversion metrics through FY2025. Preserve eight quarterly outputs, retain the discrepancy between rounded-input ADR and reported ADR, and repair the four FY2025 rolling cash windows. Distinguish the hybrid booked unit, revenue recognition timing, implied take rate and same-period financial margins.',
        'definitions':{'booking_ratios':'GBV converted from billion to million. Rounded-input ADR divides it by the supplied million Nights and Seats. Residual compares this quotient with published ADR, without forcing zero.',
          'quarter_cash':'Eight quarters in 2024 and 2025. Financial margins use quarter revenue.',
          'rolling_cash':'Each FY2025 quarter requires the latest four consecutive quarters of FCF and revenue. Compare their sums with reported TTM disclosures.'},
        'rationale':'Booking-unit scope and recognition timing limit fee inference, and quarter annualization fails under actual seasonality. A repair must combine the correct rolling window and denominator while retaining honest rounding discrepancies.'},
      'b08':{'source':'shopify-fy2025','split':'evaluation','calculate':shopify,
        'tables':{'category_economics':table(dict(ym,subscription_gp_usd_million=M,merchant_gp_usd_million=M,subscription_margin_pct=P,merchant_margin_pct=P,operating_income_usd_million=M,residual_usd_million=M,merchant_revenue_to_gmv_pct=P),['year','months'],[['b08:s01']]),
          'cash_generation':table(dict(ym,revenue_usd_million=M,fcf_usd_million=M,fcf_margin_pct=P,residual_usd_million=M),['year','months'],[['b08:s01','b08:s03']]),
          'subscription_stock_bridge':table(dict(y,mrr_usd_million=M,exit_annual_run_rate_usd_million=M,observed_annual_subscription_revenue_usd_million=M,run_rate_minus_observed_usd_million=M,run_rate_gap_pct=P),['year'],[['b08:s02','b08:s01']])},
        'sql':{'category_economics':SHOPIFY_CATEGORY,'cash_generation':SHOPIFY_CASH,'subscription_stock_bridge':SHOPIFY_STOCK},
        'starting':{'subscription_stock_bridge':SHOPIFY_STOCK.replace('12.0*s.mrr_usd_million','s.mrr_usd_million')},
        'claims':{'exit_stock_is_annual_revenue':claim('contradicted',['b08:s02','b08:s01'],'The December exit MRR annual run rate equals observed annual subscription revenue in FY2025.'),
          'merchant_margin_below_subscription':claim('supported',['b08:s01'],'Merchant solutions has a lower FY2025 gross margin percentage than subscription solutions.'),
          'exact_payments_fee_identified':claim('unresolved',['b08:s01','b08:s03'],'Merchant revenue divided by GMV identifies the exact Shopify Payments processing fee.')},
        'request':'Audit Shopify FY2025 category economics, cash conversion and subscription-stock workpapers. Preserve FY2024 and Q4, reconstruct nine-month financial flows, repair the exit-MRR annual run-rate calculation, and compare it with actual subscription revenue without presenting the difference as missing revenue. Assess whether the merchant revenue/GMV ratio identifies a payments fee.',
        'definitions':{'category_economics':'Both years, months=3 Q4, 9 first nine months, 12 annual. Category gross margins use their own revenue denominators.',
          'cash_generation':'FCF margin uses total company revenue and matched periods.',
          'subscription_stock_bridge':'Two December stocks. Twelve times exit MRR is a hypothetical annual run rate. Gap is run rate less actual annual subscription revenue, with percentage denominator actual revenue.'},
        'rationale':'A repeated December MRR stock is not an extra annual flow. Repairing its duration scaling must coexist with cumulative-flow reconstruction and unchanged category profitability, while GMV scope prevents an exact payment-fee conclusion.'}}

def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for r in rows:
            for f,v in r.items():
                if isinstance(v,(int,float)) and f not in ('year','months','quarter','reported_adr_usd'):r[f]=v*2
    yield 'scaled_observations_preserve_ratios',scaled
    changed=copy.deepcopy(data)
    if key=='b06':
        for r in changed['platform']:
            if r['year']==2025:
                r['corporate_cost_usd_million']-=20
                r['adjusted_ebitda_usd_million']-=20
        yield 'corporate_cost_changes_total_not_segments',changed
    elif key=='b07':
        for r in changed['quarters']:
            if (r['year'],r['quarter'])==(2025,1):r['operating_cash_usd_million']+=25
        for r in changed['rolling_disclosures']:r['reported_ttm_fcf_usd_million']+=25
        yield 'one_quarter_cash_changes_each_applicable_window',changed
    else:
        for r in changed['periods']:
            if r['year']==2025:
                r['subscription_revenue_usd_million']+=10
                r['subscription_cost_usd_million']+=10
        yield 'subscription_revenue_and_cost_change_preserve_profit',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        additions=copy.deepcopy(rows)
        for r in additions:r['year']+=3
        later[name]+=additions
    yield 'irrelevant_later_periods',later
