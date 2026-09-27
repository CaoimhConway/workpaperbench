"""Independent references for four disclosure-driven financial updates."""
import copy
from decimal import Decimal
from build_workflow_tasks import INTEGER, TEXT, numeric, table
from workflow_development_cases import claim
D=lambda x:Decimal(str(x))
M=numeric('usd_million',0.001)
B=numeric('usd_billion',0.000001)
P=numeric('percent')
N=numeric('million_subscriptions',0.000001)


def nvidia(data):
    financial={(r['fiscal_year'],r['months']):r for r in data['financials']}
    gross=[]
    cash=[]
    current={}
    for year in (2025,2026):
        for window,months in (('Q1',0),('Q2',3),('H1',6)):
            def f(k):return D(financial[year,6][k])-D(financial[year,3][k]) if months==0 else D(financial[year,months][k])
            revenue=f('revenue_usd_million')
            gaap=f('gaap_gross_profit_usd_million')
            adjustment=sum((f(k+'_adjustment_usd_million') for k in ('acquisition','stock','other')),D(0))
            adjusted=gaap+adjustment
            gross.append([year,window,float(revenue),float(gaap),float(adjustment),float(adjusted),float(100*gaap/revenue),float(100*adjusted/revenue),float(adjusted-f('reported_adjusted_gross_profit_usd_million'))])
            ocf=f('operating_cash_usd_million')
            purchase=f('property_and_intangible_spending_usd_million')
            principal=f('property_intangible_principal_usd_million')
            cash.append([year,window,float(ocf),float(purchase),float(principal),float(ocf-purchase-principal),float(ocf-purchase-principal-f('reported_fcf_usd_million'))])
            if year==2026:current[window]=(adjusted,revenue)
    excluded=[]
    for r in data['h20_current']:
        if r['window'] not in current:continue
        g,rev=current[r['window']]
        charge=D(r['signed_charge_usd_million'])
        excluded.append([r['window'],float(charge),float(g+charge),float(100*(g+charge)/rev),float(g+charge-D(r['reported_excluded_gross_profit_usd_million']))])
    return {'gross_profit_bases':gross,'current_h20_bridge':excluded,'cash_generation':cash}

NV_P="""WITH p AS (SELECT fiscal_year,CASE months WHEN 3 THEN 'Q2' ELSE 'H1' END window,revenue_usd_million revenue,
gaap_gross_profit_usd_million gaap,acquisition_adjustment_usd_million+stock_adjustment_usd_million+other_adjustment_usd_million adjustment,
reported_adjusted_gross_profit_usd_million reported,operating_cash_usd_million ocf,property_and_intangible_spending_usd_million purchase,
property_intangible_principal_usd_million principal,reported_fcf_usd_million fcf FROM financials WHERE fiscal_year IN (2025,2026) AND months IN (3,6)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,'Q1',a.revenue-q.revenue,a.gaap-q.gaap,a.adjustment-q.adjustment,
a.reported-q.reported,a.ocf-q.ocf,a.purchase-q.purchase,a.principal-q.principal,a.fcf-q.fcf FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.window='H1' AND q.window='Q2') """
NV_GROSS=NV_P+"""SELECT fiscal_year,window,revenue revenue_usd_million,gaap gaap_gross_profit_usd_million,adjustment gross_adjustment_usd_million,
gaap+adjustment adjusted_gross_profit_usd_million,100.0*gaap/revenue gaap_gross_margin_pct,100.0*(gaap+adjustment)/revenue adjusted_gross_margin_pct,
gaap+adjustment-reported residual_usd_million FROM periods"""
NV_H20=NV_P+"""SELECT p.window,h.signed_charge_usd_million,p.gaap+p.adjustment+h.signed_charge_usd_million excluded_gross_profit_usd_million,
100.0*(p.gaap+p.adjustment+h.signed_charge_usd_million)/p.revenue excluded_gross_margin_pct,
p.gaap+p.adjustment+h.signed_charge_usd_million-h.reported_excluded_gross_profit_usd_million residual_usd_million
FROM periods p JOIN h20_current h ON p.window=h.window WHERE p.fiscal_year=2026"""
NV_CASH=NV_P+"""SELECT fiscal_year,window,ocf operating_cash_usd_million,purchase property_intangible_spending_usd_million,
principal property_intangible_principal_usd_million,ocf-purchase-principal fcf_usd_million,ocf-purchase-principal-fcf residual_usd_million FROM periods"""


def salesforce(data):
    income={(r['fiscal_year'],r['months']):r for r in data['income']}
    adjustment={(r['fiscal_year'],r['months']):r for r in data['adjustments']}
    model=[]
    bridge=[]
    scopes=[]
    for year in (2025,2026):
        for months in (3,9,12):
            def f(rows,k):return D(rows[year,12][k])-D(rows[year,3][k]) if months==9 else D(rows[year,months][k])
            rev=f(income,'subscription_usd_million')+f(income,'professional_usd_million')
            gross=rev-f(income,'subscription_cost_usd_million')-f(income,'professional_cost_usd_million')
            op=gross-f(income,'operating_expense_usd_million')
            pretax=op+f(income,'strategic_gain_usd_million')+f(income,'other_income_usd_million')
            net=pretax+f(income,'signed_tax_usd_million')
            model.append([year,months,float(rev),float(gross),float(op),float(pretax),float(net),float(net-f(income,'reported_net_income_usd_million'))])
            ordinary=f(adjustment,'ordinary_sbc_usd_million')
            inside=f(adjustment,'sbc_inside_restructuring_usd_million')
            change=f(adjustment,'amortization_usd_million')+ordinary+f(adjustment,'restructuring_acquisition_usd_million')
            bridge.append([year,months,float(change),float(inside),float(op+change),float(100*(op+change)/rev),float(op+change-f(adjustment,'reported_adjusted_operating_usd_million'))])
    for months in (3,12):
        current=income[2026,months]
        prior=income[2025,months]
        acquired=next(r for r in data['acquired_revenue'] if r['fiscal_year']==2026 and r['months']==months)
        cr=D(current['subscription_usd_million'])+D(current['professional_usd_million'])
        pr=D(prior['subscription_usd_million'])+D(prior['professional_usd_million'])
        ar=D(acquired['total_revenue_usd_million'])
        sub=D(current['subscription_usd_million'])-D(acquired['subscription_usd_million'])
        scopes.append([months,float(cr),float(pr),float(ar),float(cr-ar),float(100*(cr/pr-1)),float(100*((cr-ar)/pr-1)),float(sub)])
    return {'income_model':model,'operating_adjustment_bridge':bridge,'acquisition_scope':scopes}

SF_P="""WITH p AS (SELECT i.*,a.amortization_usd_million,a.ordinary_sbc_usd_million,a.restructuring_acquisition_usd_million,
a.sbc_inside_restructuring_usd_million,a.reported_adjusted_operating_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.subscription_usd_million-q.subscription_usd_million,
a.professional_usd_million-q.professional_usd_million,a.subscription_cost_usd_million-q.subscription_cost_usd_million,
a.professional_cost_usd_million-q.professional_cost_usd_million,a.operating_expense_usd_million-q.operating_expense_usd_million,
a.reported_operating_usd_million-q.reported_operating_usd_million,a.strategic_gain_usd_million-q.strategic_gain_usd_million,
a.other_income_usd_million-q.other_income_usd_million,a.signed_tax_usd_million-q.signed_tax_usd_million,a.reported_net_income_usd_million-q.reported_net_income_usd_million,
a.amortization_usd_million-q.amortization_usd_million,a.ordinary_sbc_usd_million-q.ordinary_sbc_usd_million,
a.restructuring_acquisition_usd_million-q.restructuring_acquisition_usd_million,a.sbc_inside_restructuring_usd_million-q.sbc_inside_restructuring_usd_million,
a.reported_adjusted_operating_usd_million-q.reported_adjusted_operating_usd_million FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3),
base AS (SELECT *,subscription_usd_million+professional_usd_million rev,
subscription_usd_million+professional_usd_million-subscription_cost_usd_million-professional_cost_usd_million gp FROM periods),
computed AS (SELECT *,gp-operating_expense_usd_million op FROM base) """
SF_MODEL=SF_P+"""SELECT fiscal_year,months,rev revenue_usd_million,gp gross_profit_usd_million,op operating_income_usd_million,
op+strategic_gain_usd_million+other_income_usd_million pretax_usd_million,
op+strategic_gain_usd_million+other_income_usd_million+signed_tax_usd_million net_income_usd_million,
op+strategic_gain_usd_million+other_income_usd_million+signed_tax_usd_million-reported_net_income_usd_million residual_usd_million FROM computed"""
SF_BRIDGE=SF_P+"""SELECT fiscal_year,months,amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million exclusion_usd_million,
sbc_inside_restructuring_usd_million already_in_restructuring_sbc_usd_million,
op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million adjusted_operating_usd_million,
100.0*(op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million)/rev adjusted_margin_pct,
op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million-reported_adjusted_operating_usd_million residual_usd_million FROM computed"""
SF_SCOPE="""SELECT c.months,c.subscription_usd_million+c.professional_usd_million current_revenue_usd_million,
p.subscription_usd_million+p.professional_usd_million prior_revenue_usd_million,a.total_revenue_usd_million acquired_revenue_usd_million,
c.subscription_usd_million+c.professional_usd_million-a.total_revenue_usd_million current_ex_disclosed_acquisition_usd_million,
100.0*((c.subscription_usd_million+c.professional_usd_million)/(p.subscription_usd_million+p.professional_usd_million)-1) reported_growth_pct,
100.0*((c.subscription_usd_million+c.professional_usd_million-a.total_revenue_usd_million)/(p.subscription_usd_million+p.professional_usd_million)-1) arithmetic_ex_acquisition_growth_pct,
c.subscription_usd_million-a.subscription_usd_million subscription_ex_acquisition_usd_million FROM income c JOIN income p ON c.months=p.months AND c.fiscal_year=2026 AND p.fiscal_year=2025
JOIN acquired_revenue a ON a.fiscal_year=c.fiscal_year AND a.months=c.months WHERE c.months IN (3,12)"""


def disney(data):
    segments={(r['fiscal_year'],r['months'],r['segment']):r for r in data['segments']}
    bases={(r['fiscal_year'],r['months']):r for r in data['reconciliation']}
    model=[]
    bridge=[]
    for year in (2024,2025):
        for months in (3,9,12):
            def f(k):return D(bases[year,12][k])-D(bases[year,3][k]) if months==9 else D(bases[year,months][k])
            revenue=D(0)
            operating=D(0)
            for name in ('Entertainment','Sports','Experiences'):
                def s(k):return D(segments[year,12,name][k])-D(segments[year,3,name][k]) if months==9 else D(segments[year,months,name][k])
                rev,op=s('revenue_usd_million'),s('operating_income_usd_million')
                model.append([year,months,name,float(rev),float(op),float(100*op/rev)])
                revenue+=rev
                operating+=op
            add=sum((f(k+'_usd_million') for k in ('corporate','india_loss','restructuring','other_expense','interest','amortization')),D(0))
            pretax=f('pretax_income_usd_million')
            bridge.append([year,months,float(revenue),float(f('revenue_eliminations_usd_million')),float(revenue+f('revenue_eliminations_usd_million')),float(operating),float(pretax),float(add),float(pretax+add-operating),float(operating-f('reported_segment_operating_usd_million'))])
    counts={(r['economic_date'],r['service']):D(r['subscriptions_million']) for r in data['subscriptions']}
    stock=[]
    for date in ('2025-06-28','2025-09-27'):
        d,h=counts[date,'Disney+'],counts[date,'Hulu']
        stock.append([date,float(d),float(h),float(d+h),float(d+h-counts['2025-06-28','Disney+']-counts['2025-06-28','Hulu'])])
    return {'segment_model':model,'consolidated_bridge':bridge,'service_subscriptions':stock}

DIS_SEG="""WITH p AS (SELECT * FROM segments WHERE fiscal_year IN (2024,2025)),periods AS (SELECT * FROM p UNION ALL
SELECT a.fiscal_year,9,a.segment,a.revenue_usd_million-q.revenue_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment AND a.months=12 AND q.months=3) """
DIS_MODEL=DIS_SEG+"""SELECT fiscal_year,months,segment,revenue_usd_million,operating_income_usd_million,100.0*operating_income_usd_million/revenue_usd_million margin_pct FROM periods"""
DIS_BRIDGE=DIS_SEG+""",r AS (SELECT * FROM reconciliation WHERE fiscal_year IN (2024,2025)),recons AS (SELECT * FROM r UNION ALL SELECT a.fiscal_year,9,
a.pretax_income_usd_million-q.pretax_income_usd_million,a.corporate_usd_million-q.corporate_usd_million,a.india_loss_usd_million-q.india_loss_usd_million,
a.restructuring_usd_million-q.restructuring_usd_million,a.other_expense_usd_million-q.other_expense_usd_million,a.interest_usd_million-q.interest_usd_million,
a.amortization_usd_million-q.amortization_usd_million,a.reported_segment_operating_usd_million-q.reported_segment_operating_usd_million,
a.revenue_eliminations_usd_million-q.revenue_eliminations_usd_million FROM r a JOIN r q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3)
SELECT p.fiscal_year,p.months,SUM(p.revenue_usd_million) gross_segment_revenue_usd_million,r.revenue_eliminations_usd_million,
SUM(p.revenue_usd_million)+r.revenue_eliminations_usd_million consolidated_revenue_usd_million,SUM(p.operating_income_usd_million) segment_operating_usd_million,
r.pretax_income_usd_million,r.corporate_usd_million+r.india_loss_usd_million+r.restructuring_usd_million+r.other_expense_usd_million+r.interest_usd_million+r.amortization_usd_million signed_bridge_usd_million,
r.pretax_income_usd_million+r.corporate_usd_million+r.india_loss_usd_million+r.restructuring_usd_million+r.other_expense_usd_million+r.interest_usd_million+r.amortization_usd_million-SUM(p.operating_income_usd_million) pretax_bridge_residual_usd_million,
SUM(p.operating_income_usd_million)-r.reported_segment_operating_usd_million segment_sum_residual_usd_million FROM periods p JOIN recons r USING(fiscal_year,months) GROUP BY p.fiscal_year,p.months"""
DIS_STOCK="""WITH p AS (SELECT economic_date,MAX(CASE service WHEN 'Disney+' THEN subscriptions_million END) d,MAX(CASE service WHEN 'Hulu' THEN subscriptions_million END) h
FROM subscriptions WHERE economic_date IN ('2025-06-28','2025-09-27') GROUP BY economic_date)
SELECT c.economic_date,c.d disney_subscriptions_million,c.h hulu_subscriptions_million,c.d+c.h total_service_subscriptions_million,c.d+c.h-p.d-p.h sequential_change_million FROM p c JOIN p ON p.economic_date='2025-06-28'"""


def amex(data):
    model=[]
    for r in data['income']:
        if r['period'] not in ('Q4FY2025','Q3FY2025','Q2FY2025','Q1FY2025','Q4FY2024','FY2025','FY2024'):continue
        revenue=sum((D(r[k+'_usd_million']) for k in ('discount','card_fees','service_other','net_interest')),D(0))
        pretax=revenue-D(r['provisions_usd_million'])-D(r['expense_usd_million'])
        net=pretax-D(r['tax_usd_million'])
        model.append([r['period'],float(revenue),float(pretax),float(net),float(revenue-D(r['revenue_usd_million'])),float(net-D(r['net_income_usd_million']))])
    growth=[]
    attribution=[]
    for r in data['comparison']:
        if r['window'] not in ('Q4','FY'):continue
        c,p,f=[D(r[k+'_billed_usd_billion']) for k in ('current','prior','fx_prior')]
        cr,pr,fr=[D(r[k+'_revenue_usd_million']) for k in ('current','prior','fx_prior')]
        growth.append([r['window'],float(100*(c/p-1)),float(100*(c/f-1)),float(100*(cr/pr-1)),float(100*(cr/fr-1)),float(D(r['current_network_usd_billion'])-c),float(D(r['prior_network_usd_billion'])-p)])
        prefix='Q4FY' if r['window']=='Q4' else 'FY'
        prior=next(i for i in data['income'] if i['period']==prefix+'2024')
        current=next(i for i in data['income'] if i['period']==prefix+'2025')
        delta=cr-pr
        for measure in ('discount','card_fees','service_other','net_interest'):
            change=D(current[measure+'_usd_million'])-D(prior[measure+'_usd_million'])
            attribution.append([r['window'],measure,float(change),float(100*change/delta)])
    return {'income_model':model,'currency_and_network':growth,'revenue_growth_bridge':attribution}

AX_MODEL="""WITH p AS (SELECT *,discount_usd_million+card_fees_usd_million+service_other_usd_million+net_interest_usd_million computed FROM income
WHERE period IN ('Q4FY2025','Q3FY2025','Q2FY2025','Q1FY2025','Q4FY2024','FY2025','FY2024')) SELECT period,computed revenue_usd_million,
computed-provisions_usd_million-expense_usd_million pretax_usd_million,computed-provisions_usd_million-expense_usd_million-tax_usd_million net_income_usd_million,
computed-revenue_usd_million revenue_residual_usd_million,computed-provisions_usd_million-expense_usd_million-tax_usd_million-net_income_usd_million net_residual_usd_million FROM p"""
AX_GROWTH="""SELECT window,100.0*(current_billed_usd_billion/prior_billed_usd_billion-1) billed_reported_growth_pct,
100.0*(current_billed_usd_billion/fx_prior_billed_usd_billion-1) billed_fx_growth_pct,100.0*(current_revenue_usd_million/prior_revenue_usd_million-1) revenue_reported_growth_pct,
100.0*(current_revenue_usd_million/fx_prior_revenue_usd_million-1) revenue_fx_growth_pct,current_network_usd_billion-current_billed_usd_billion current_processed_usd_billion,
prior_network_usd_billion-prior_billed_usd_billion prior_processed_usd_billion FROM comparison WHERE window IN ('FY','Q4')"""
AX_BRIDGE="""WITH p AS (SELECT period,'discount' measure,discount_usd_million amount FROM income UNION ALL SELECT period,'card_fees',card_fees_usd_million FROM income
UNION ALL SELECT period,'service_other',service_other_usd_million FROM income UNION ALL SELECT period,'net_interest',net_interest_usd_million FROM income)
SELECT g.window,c.measure,c.amount-p.amount change_usd_million,100.0*(c.amount-p.amount)/(g.current_revenue_usd_million-g.prior_revenue_usd_million) contribution_to_revenue_growth_pct
FROM comparison g JOIN p c ON c.period=(CASE g.window WHEN 'Q4' THEN 'Q4FY' ELSE 'FY' END)||'2025' JOIN p ON p.period=(CASE g.window WHEN 'Q4' THEN 'Q4FY' ELSE 'FY' END)||'2024' AND p.measure=c.measure WHERE g.window IN ('FY','Q4')"""


def specifications():
    period={'fiscal_year':INTEGER,'months':INTEGER}
    return {
      'a07':{'source':'nvidia-q2fy2026','split':'evaluation','calculate':nvidia,
        'tables':{'gross_profit_bases':table({'fiscal_year':INTEGER,'window':TEXT,'revenue_usd_million':M,'gaap_gross_profit_usd_million':M,'gross_adjustment_usd_million':M,'adjusted_gross_profit_usd_million':M,'gaap_gross_margin_pct':P,'adjusted_gross_margin_pct':P,'residual_usd_million':M},['fiscal_year','window'],[['a07:s01']]),
          'current_h20_bridge':table({'window':TEXT,'signed_charge_usd_million':M,'excluded_gross_profit_usd_million':M,'excluded_gross_margin_pct':P,'residual_usd_million':M},['window'],[['a07:s01']]),
          'cash_generation':table({'fiscal_year':INTEGER,'window':TEXT,'operating_cash_usd_million':M,'property_intangible_spending_usd_million':M,'property_intangible_principal_usd_million':M,'fcf_usd_million':M,'residual_usd_million':M},['fiscal_year','window'],[['a07:s02']])},
        'sql':{'gross_profit_bases':NV_GROSS,'current_h20_bridge':NV_H20,'cash_generation':NV_CASH},
        'starting':{'current_h20_bridge':NV_H20.replace('p.gaap+p.adjustment+h.signed_charge_usd_million','p.gaap+p.adjustment-h.signed_charge_usd_million')},
        'claims':{'release_raises_excluded_margin':claim('contradicted',['a07:s01'],'Removing the Q2 inventory release raises the H20-excluded gross margin above standard non-GAAP margin.'),
          'china_zero_means_global_zero':claim('contradicted',['a07:s03'],'No current Q2 China H20 sales means current Q2 worldwide H20 sales were zero.'),
          'exact_future_china_shipments':claim('unresolved',['a07:s03'],'The Q3 guidance assumption establishes exact subsequently realized China H20 shipments.')},
        'request':'Update NVIDIA through Q2FY2026. Reconstruct Q1 for both years from first-half and Q2 inputs, retain standard gross-profit bases, and add the current-year H20 charge/release bridge without treating missing prior exclusions as zero. Reconcile issuer cash generation and assess the geographical and forward-looking H20 statements.',
        'definitions':{'gross_profit_bases':'Six rows: Q1, Q2 and H1 in both fiscal years. Derive Q1 from H1 less Q2. Standard adjustments are signed additions. Preserve rounding residuals.',
          'current_h20_bridge':'Three current-year rows only. Remove the signed H20 charge or release from the standard gross-profit basis. No prior-year H20 row is requested.',
          'cash_generation':'Same six periods. Issuer FCF subtracts property/intangible purchases and disclosed property/intangible principal. Residual compares recomputed with reported FCF on the same cumulative-difference basis.'},
        'rationale':'Inventory releases reverse the sign of an exclusion while multiple margin bases coexist. Half-year reconstruction, cash principal and absent geographic observations make this an interacting update rather than a revenue lookup.'},
      'a08':{'source':'salesforce-fy2026','split':'evaluation','calculate':salesforce,
        'tables':{'income_model':table(dict(period,revenue_usd_million=M,gross_profit_usd_million=M,operating_income_usd_million=M,pretax_usd_million=M,net_income_usd_million=M,residual_usd_million=M),['fiscal_year','months'],[['a08:s01']]),
          'operating_adjustment_bridge':table(dict(period,exclusion_usd_million=M,already_in_restructuring_sbc_usd_million=M,adjusted_operating_usd_million=M,adjusted_margin_pct=P,residual_usd_million=M),['fiscal_year','months'],[['a08:s01','a08:s02']]),
          'acquisition_scope':table({'months':INTEGER,'current_revenue_usd_million':M,'prior_revenue_usd_million':M,'acquired_revenue_usd_million':M,'current_ex_disclosed_acquisition_usd_million':M,'reported_growth_pct':P,'arithmetic_ex_acquisition_growth_pct':P,'subscription_ex_acquisition_usd_million':M},['months'],[['a08:s01','a08:s03']])},
        'sql':{'income_model':SF_MODEL,'operating_adjustment_bridge':SF_BRIDGE,'acquisition_scope':SF_SCOPE},
        'starting':{'operating_adjustment_bridge':SF_BRIDGE.replace('op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million','op+amortization_usd_million+ordinary_sbc_usd_million+restructuring_acquisition_usd_million+sbc_inside_restructuring_usd_million')},
        'claims':{'annual_acquisition_same_as_q4':claim('supported',['a08:s03'],'The disclosed FY2026 acquisition revenue contribution equals its disclosed Q4 contribution.'),
          'offering_rename_changes_allocation':claim('contradicted',['a08:s03'],'The Q3 service-offering rename changed revenue allocation.'),
          'exact_organic_cc_growth':claim('unresolved',['a08:s03'],'Subtracting the disclosed acquired revenue uniquely identifies exact organic constant-currency growth.')},
        'request':'Update Salesforce FY2026 earnings through Q4, preserve Q4 and annual comparisons and reconstruct first nine months. Reconcile operating and below-operating income, avoid double-counting restructuring SBC, and produce a labeled acquisition-scope revenue bridge without overstating an organic currency-adjusted conclusion.',
        'definitions':{'income_model':'Three, nine and twelve months in each fiscal year. months=3 is Q4. Signed tax adds to pretax income.',
          'operating_adjustment_bridge':'Ordinary SBC excludes SBC already in restructuring. Report the latter for audit but add each exclusion once. Residual compares with the matching reported adjusted operating basis.',
          'acquisition_scope':'Q4 and annual current and prior revenue, disclosed acquisition contribution, arithmetic current less acquisition, both growth rates and current subscription less disclosed acquired subscription. This is not labeled exact organic growth.'},
        'rationale':'A November acquisition has the same cumulative and quarter contribution, while overlapping SBC labels invite a duplicate exclusion. Historical preservation and a bounded acquisition attribution interact with earnings reconstruction.'},
      'a09':{'source':'disney-fy2025','split':'evaluation','calculate':disney,
        'tables':{'segment_model':table(dict(period,segment=TEXT,revenue_usd_million=M,operating_income_usd_million=M,margin_pct=P),['fiscal_year','months','segment'],[['a09:s01']]),
          'consolidated_bridge':table(dict(period,gross_segment_revenue_usd_million=M,revenue_eliminations_usd_million=M,consolidated_revenue_usd_million=M,segment_operating_usd_million=M,pretax_income_usd_million=M,signed_bridge_usd_million=M,pretax_bridge_residual_usd_million=M,segment_sum_residual_usd_million=M),['fiscal_year','months'],[['a09:s01']]),
          'service_subscriptions':table({'economic_date':TEXT,'disney_subscriptions_million':N,'hulu_subscriptions_million':N,'total_service_subscriptions_million':N,'sequential_change_million':N},['economic_date'],[['a09:s02']])},
        'sql':{'segment_model':DIS_MODEL,'consolidated_bridge':DIS_BRIDGE,'service_subscriptions':DIS_STOCK},
        'starting':{'consolidated_bridge':DIS_BRIDGE.replace('SUM(p.revenue_usd_million)+r.revenue_eliminations_usd_million consolidated','SUM(p.revenue_usd_million) consolidated')},
        'claims':{'india_is_still_consolidated_q4':claim('contradicted',['a09:s02'],'The current Q4 includes Star India as a consolidated operating business.'),
          'sum_is_unique_people':claim('contradicted',['a09:s02'],'The sum of Disney+ and Hulu subscriptions measures unique people.'),
          'exact_constant_scope_dtc_growth':claim('unresolved',['a09:s02','a09:s03'],'The supplied evidence uniquely determines exact constant-scope DTC revenue growth excluding Star India.')},
        'request':'Update Disney FY2025 segment and consolidated models through Q4 and derive first nine months for both years. Reconcile intersegment revenue and segment profit to GAAP pretax income. Keep the subscription comparison sequential and labeled as service subscriptions, and assess the change from consolidated Star India to equity-method ownership.',
        'definitions':{'segment_model':'Three segments for Q4, first nine months and annual in both years, with segment operating margin on segment revenue.',
          'consolidated_bridge':'Gross segment revenue plus signed eliminations is consolidated revenue. The signed pretax bridge adds disclosed exclusions to pretax income. Show both reconciliation residuals.',
          'service_subscriptions':'June and September 2025 service totals and their change from June. Neither service totals nor changes are unique people or a revenue flow.'},
        'rationale':'Actual deconsolidation changes the financial narrative, while intersegment revenue and bundled subscription identities require preserving different populations. A usable update must answer the reconciliations without fabricating an organic comparison.'},
      'a10':{'source':'amex-fy2025','split':'evaluation','calculate':amex,
        'tables':{'income_model':table({'period':TEXT,'revenue_usd_million':M,'pretax_usd_million':M,'net_income_usd_million':M,'revenue_residual_usd_million':M,'net_residual_usd_million':M},['period'],[['a10:s01']]),
          'currency_and_network':table({'window':TEXT,'billed_reported_growth_pct':P,'billed_fx_growth_pct':P,'revenue_reported_growth_pct':P,'revenue_fx_growth_pct':P,'current_processed_usd_billion':B,'prior_processed_usd_billion':B},['window'],[['a10:s02','a10:s03']]),
          'revenue_growth_bridge':table({'window':TEXT,'measure':TEXT,'change_usd_million':M,'contribution_to_revenue_growth_pct':P},['window','measure'],[['a10:s01','a10:s03']])},
        'sql':{'income_model':AX_MODEL,'currency_and_network':AX_GROWTH,'revenue_growth_bridge':AX_BRIDGE},
        'starting':{'currency_and_network':AX_GROWTH.replace('current_revenue_usd_million/fx_prior_revenue_usd_million','fx_prior_revenue_usd_million/prior_revenue_usd_million')},
        'claims':{'fx_restates_prior':claim('supported',['a10:s02','a10:s03'],'The stated FX comparison restates prior-year amounts at current-period rates.'),
          'billed_equals_network':claim('contradicted',['a10:s02'],'Billed business and total network volume have identical payment-product scope.'),
          'exact_discount_price_effect':claim('unresolved',['a10:s01','a10:s02'],'The supplied totals uniquely quantify the causal pricing contribution to discount-revenue growth.')},
        'request':'Update American Express FY2025 payment economics using the seven-period income statements and both release and statistical supplement. Reconcile revenue to earnings, attribute annual and Q4 revenue growth by component, and produce reported/FX growth plus the implied processed-volume bridge while preserving source scope.',
        'definitions':{'income_model':'All seven stated periods. Recompute revenue from four components, then pretax and net income, preserving source rounding residuals.',
          'currency_and_network':'Annual and Q4 comparisons use current reported numerators and the matching prior reported or prior FX-adjusted denominator. Processed volume is network less billed business in USD billion.',
          'revenue_growth_bridge':'Four component changes, FY2025 less FY2024 and Q4FY2025 less Q4FY2024. Contributions divide by matching total reported-revenue change.'},
        'rationale':'A payment model must reconcile two primary disclosures, translate the correct period, distinguish issued from processed card flows and avoid treating aggregate fee growth as an identified price effect.'}}


def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for row in rows:
            for field,value in row.items():
                if isinstance(value,(int,float)) and field not in ('fiscal_year','months'):row[field]=value*2
    yield 'scaled_amounts_preserve_ratios',scaled
    changed=copy.deepcopy(data)
    if key=='a07':
        for r in changed['financials']:
            if r['fiscal_year']==2026:
                r['gaap_gross_profit_usd_million']+=20
                r['reported_adjusted_gross_profit_usd_million']+=20
        for r in changed['h20_current']:
            if r['window'] in ('Q2','H1'):
                r['signed_charge_usd_million']-=20
        yield 'inventory_release_changes_standard_not_excluded_profit',changed
    elif key=='a08':
        for r in changed['adjustments']:
            if r['fiscal_year']==2026:r['sbc_inside_restructuring_usd_million']+=1
        yield 'overlapping_sbc_label_is_not_an_extra_exclusion',changed
    elif key=='a09':
        for r in changed['reconciliation']:
            if r['fiscal_year']==2025:
                r['corporate_usd_million']+=10
                r['pretax_income_usd_million']-=10
        yield 'corporate_charge_changes_gaap_not_segment_results',changed
    else:
        for r in changed['income']:
            if r['period'] in ('Q4FY2025','FY2025'):
                r['card_fees_usd_million']+=10
                r['expense_usd_million']+=10
                r['revenue_usd_million']+=10
        for r in changed['comparison']:r['current_revenue_usd_million']+=10
        yield 'fee_and_expense_change_preserves_net_income',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        if name in ('h20_current','reported_q1'):continue
        extra=copy.deepcopy(rows)
        for r in extra:
            if 'fiscal_year' in r:r['fiscal_year']+=5
            elif 'period' in r:r['period']='unrequested_'+r['period']
            elif 'economic_date' in r:r['economic_date']='2029-12-31'
            elif 'window' in r:r['window']='unrequested_'+r['window']
        later[name]+=extra
    yield 'irrelevant_later_disclosures',later
