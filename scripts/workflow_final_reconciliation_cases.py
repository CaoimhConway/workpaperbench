"""Source-grounded share, bank-basis and forecast reconciliation references."""
import copy
from decimal import Decimal
from build_workflow_tasks import TEXT, INTEGER, numeric, table
from workflow_development_cases import claim
D=lambda x:Decimal(str(x))
M=numeric('usd_million',0.001)
K=numeric('usd_thousand',0.001)
P=numeric('percent')
U=numeric('usd_per_share')

def broadcom(data):
    periods=('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024')
    income=[]
    shares=[]
    for r in data['income_bases']:
        if r['period'] not in periods:continue
        gaap,reported,gs,ns=[D(r[f]) for f in ('gaap_income_usd_million','reported_adjusted_income_usd_million','gaap_shares_million','adjusted_shares_million')]
        change=sum((D(a['signed_income_adjustment_usd_million']) for a in data['income_adjustments'] if a['period']==r['period']),D(0))
        adjusted=gaap+change
        income.append([r['period'],float(gaap),float(change),float(adjusted),float(adjusted-reported)])
        shares.append([r['period'],float(gs),float(ns),float(gaap/gs),float(gaap/gs-D(r['reported_gaap_eps_usd'])),float(adjusted/ns),float(adjusted/gs),float(adjusted/ns-adjusted/gs)])
    index={(r['period'],r['segment']):D(r['revenue_usd_million']) for r in data['segments'] if r['period'] in periods}
    segments=[]
    for window in ('FY','Q4FY'):
        total=sum((index[window+'2025',s]-index[window+'2024',s] for s in ('Semiconductor','Infrastructure software')),D(0))
        for s in ('Semiconductor','Infrastructure software'):
            p,c=index[window+'2024',s],index[window+'2025',s]
            segments.append([window,s,float(p),float(c),float(c-p),float(100*(c-p)/total)])
    return {'income_reconciliation':income,'share_basis':shares,'segment_growth_bridge':segments}

BROADCOM_INCOME="""SELECT b.period,b.gaap_income_usd_million,SUM(a.signed_income_adjustment_usd_million) signed_adjustment_usd_million,
b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million) adjusted_income_usd_million,
b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million)-b.reported_adjusted_income_usd_million residual_usd_million
FROM income_bases b JOIN income_adjustments a ON b.period=a.period WHERE b.period IN ('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024') GROUP BY b.period"""
BROADCOM_SHARES="""WITH p AS (SELECT b.*,b.gaap_income_usd_million+SUM(a.signed_income_adjustment_usd_million) adjusted FROM income_bases b
JOIN income_adjustments a ON b.period=a.period GROUP BY b.period)
SELECT period,gaap_shares_million,adjusted_shares_million,1.0*gaap_income_usd_million/gaap_shares_million computed_gaap_eps_usd,
1.0*gaap_income_usd_million/gaap_shares_million-reported_gaap_eps_usd gaap_eps_rounding_residual_usd,
1.0*adjusted/adjusted_shares_million computed_adjusted_eps_usd,1.0*adjusted/gaap_shares_million adjusted_income_over_gaap_shares_usd,
1.0*adjusted/adjusted_shares_million-1.0*adjusted/gaap_shares_million denominator_effect_usd
FROM p WHERE period IN ('Q4FY2025','Q3FY2025','Q4FY2024','FY2025','FY2024')"""
BROADCOM_SEGMENTS="""WITH p AS (SELECT CASE WHEN period LIKE 'Q4%' THEN 'Q4FY' ELSE 'FY' END window,period,segment,revenue_usd_million FROM segments
WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025')),totals AS (SELECT window,SUM(CASE WHEN period LIKE '%2025' THEN revenue_usd_million ELSE -revenue_usd_million END) delta FROM p GROUP BY window)
SELECT c.window,c.segment,p.revenue_usd_million prior_usd_million,c.revenue_usd_million current_usd_million,c.revenue_usd_million-p.revenue_usd_million change_usd_million,
100.0*(c.revenue_usd_million-p.revenue_usd_million)/t.delta contribution_to_total_growth_pct FROM p c JOIN p ON c.window=p.window AND c.segment=p.segment AND c.period LIKE '%2025' AND p.period LIKE '%2024' JOIN totals t ON t.window=c.window"""

def jpm(data):
    basis=[]
    items=[]
    for r in data['bank_bases']:
        if r['period'] not in ('FY2025','Q4FY2025'):continue
        rev,fte,expense,legal=[D(r[f]) for f in ('managed_revenue_usd_million','fte_adjustment_usd_million','expense_usd_million','legal_expense_usd_million')]
        basis.append([r['period'],float(rev),float(rev-fte),float(fte),float(100*expense/rev),float(100*(expense-legal)/rev),float(D(r['nii_usd_million'])+D(r['nir_usd_million'])-rev)])
    selected=[r for r in data['significant_items'] if r['period'] in ('FY2025','Q4FY2025')]
    for r in selected:
        reserve,after,net,change=[D(r[f]) for f in ('apple_pretax_reserve_usd_million','apple_aftertax_effect_usd_million','reported_net_income_usd_million','net_income_exclusion_change_usd_million')]
        items.append([r['period'],float(reserve),float(after),float(reserve-after),float(change),float(net+change),float(net+change-D(r['reported_adjusted_net_income_usd_million']))])
    annual=next(r for r in selected if r['period']=='FY2025')
    detail=next(r for r in data['annual_significant_details'] if r['period']=='FY2025')
    apple_effect=D(annual['apple_aftertax_effect_usd_million'])
    total=D(annual['net_income_exclusion_change_usd_million'])
    tax=D(detail['corporate_tax_benefit_usd_million'])
    implied=apple_effect-tax-total
    components=[['apple_reserve',float(apple_effect),'printed_after_tax'],['first_republic_gain',float(-implied),'derived_after_tax'],['corporate_tax_benefit',float(-tax),'printed_after_tax']]
    return {'bank_basis_bridge':basis,'significant_item_bridge':items,'annual_exclusion_components':components}

JPM_BASIS="""SELECT period,managed_revenue_usd_million,managed_revenue_usd_million-fte_adjustment_usd_million printed_input_reported_basis_estimate_usd_million,
fte_adjustment_usd_million,100.0*expense_usd_million/managed_revenue_usd_million overhead_pct,
100.0*(expense_usd_million-legal_expense_usd_million)/managed_revenue_usd_million adjusted_overhead_pct,
nii_usd_million+nir_usd_million-managed_revenue_usd_million managed_revenue_residual_usd_million FROM bank_bases WHERE period IN ('Q4FY2025','FY2025')"""
JPM_ITEMS="""SELECT period,apple_pretax_reserve_usd_million,apple_aftertax_effect_usd_million,
apple_pretax_reserve_usd_million-apple_aftertax_effect_usd_million apple_tax_shield_usd_million,net_income_exclusion_change_usd_million,
reported_net_income_usd_million+net_income_exclusion_change_usd_million printed_input_adjusted_net_income_usd_million,
reported_net_income_usd_million+net_income_exclusion_change_usd_million-reported_adjusted_net_income_usd_million rounding_residual_usd_million
FROM significant_items WHERE period IN ('Q4FY2025','FY2025')"""
JPM_COMPONENTS="""WITH a AS (SELECT * FROM significant_items WHERE period='FY2025'),d AS (SELECT * FROM annual_significant_details WHERE period='FY2025')
SELECT 'apple_reserve' measure,apple_aftertax_effect_usd_million signed_aftertax_exclusion_usd_million,'printed_after_tax' origin FROM a
UNION ALL SELECT 'first_republic_gain',-(apple_aftertax_effect_usd_million-d.corporate_tax_benefit_usd_million-net_income_exclusion_change_usd_million),'derived_after_tax' FROM a CROSS JOIN d
UNION ALL SELECT 'corporate_tax_benefit',-corporate_tax_benefit_usd_million,'printed_after_tax' FROM d"""

def netflix(data):
    regions=[]
    for r in data['regional_q4']:
        c,p,fx,ch,ph=[D(r[f]) for f in ('current_revenue_usd_thousand','prior_revenue_usd_thousand','currency_adjustment_usd_thousand','current_hedging_exclusion_usd_thousand','prior_hedging_exclusion_usd_thousand')]
        cc=c+fx+ch
        prior=p+ph
        regions.append([r['region'],float(cc),float(prior),float(100*(c/p-1)),float(100*(cc/prior-1)),float(fx),float(ch-ph)])
    annual=next(r for r in data['annual_margin'] if r['year']==2025)
    rev,exp,rfx,efx=[D(annual[f]) for f in ('revenue_usd_thousand','expense_usd_thousand','revenue_fx_usd_thousand','expense_fx_usd_thousand')]
    op=rev-exp
    adjrev=rev-rfx
    adjexp=exp-efx
    adjop=adjrev-adjexp
    margins=[[2025,float(op),float(adjop),float(100*op/rev),float(100*adjop/adjrev),float(10000*(adjop/adjrev-op/rev)),float(adjop-D(annual['reported_adjusted_operating_usd_thousand']))]]
    forecast=[]
    for r in data['forecasts']:
        if r['year']!=2026:continue
        f=D(r['revenue_usd_million'])
        operating=f*D(r['target_operating_margin_pct'])/100
        forecast.append([2026,r['bound'],float(f),float(100*(1000*f/rev-1)),float(operating),float(100*(1000*operating/op-1)),float(D(r['included_acquisition_expense_usd_million']))])
    return {'regional_currency':regions,'annual_currency_margin':margins,'forecast_bounds':forecast}

NETFLIX_REGIONS="""SELECT region,current_revenue_usd_thousand+currency_adjustment_usd_thousand+current_hedging_exclusion_usd_thousand cc_current_usd_thousand,
prior_revenue_usd_thousand+prior_hedging_exclusion_usd_thousand unhedged_prior_usd_thousand,
100.0*(current_revenue_usd_thousand/prior_revenue_usd_thousand-1) reported_growth_pct,
100.0*((current_revenue_usd_thousand+currency_adjustment_usd_thousand+current_hedging_exclusion_usd_thousand)/(prior_revenue_usd_thousand+prior_hedging_exclusion_usd_thousand)-1) cc_growth_pct,
currency_adjustment_usd_thousand, current_hedging_exclusion_usd_thousand-prior_hedging_exclusion_usd_thousand hedging_exclusion_change_usd_thousand FROM regional_q4"""
NETFLIX_MARGIN="""SELECT CAST(year AS INTEGER) year,revenue_usd_thousand-expense_usd_thousand operating_income_usd_thousand,
revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand adjusted_operating_income_usd_thousand,
100.0*(revenue_usd_thousand-expense_usd_thousand)/revenue_usd_thousand reported_margin_pct,
100.0*(revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand)/(revenue_usd_thousand-revenue_fx_usd_thousand) adjusted_margin_pct,
10000.0*((revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand)/(revenue_usd_thousand-revenue_fx_usd_thousand)-(revenue_usd_thousand-expense_usd_thousand)/revenue_usd_thousand) margin_change_bp,
revenue_usd_thousand-revenue_fx_usd_thousand-expense_usd_thousand+expense_fx_usd_thousand-reported_adjusted_operating_usd_thousand residual_usd_thousand
FROM annual_margin WHERE year=2025"""
NETFLIX_FORECAST="""SELECT CAST(f.year AS INTEGER) year,f.bound,f.revenue_usd_million,
100.0*(1000.0*f.revenue_usd_million/a.revenue_usd_thousand-1) implied_reported_revenue_growth_pct,
f.revenue_usd_million*f.target_operating_margin_pct/100.0 implied_operating_income_usd_million,
100.0*(10.0*f.revenue_usd_million*f.target_operating_margin_pct/(a.revenue_usd_thousand-a.expense_usd_thousand)-1) implied_operating_growth_pct,
f.included_acquisition_expense_usd_million FROM forecasts f CROSS JOIN annual_margin a WHERE f.year=2026 AND a.year=2025"""

def specifications():
    return {
      'c08':{'source':'broadcom-fy2025','split':'evaluation','calculate':broadcom,
        'tables':{'income_reconciliation':table({'period':TEXT,'gaap_income_usd_million':M,'signed_adjustment_usd_million':M,'adjusted_income_usd_million':M,'residual_usd_million':M},['period'],[['c08:s01']]),
          'share_basis':table({'period':TEXT,'gaap_shares_million':numeric('million_shares'),'adjusted_shares_million':numeric('million_shares'),'computed_gaap_eps_usd':U,'gaap_eps_rounding_residual_usd':U,'computed_adjusted_eps_usd':U,'adjusted_income_over_gaap_shares_usd':U,'denominator_effect_usd':U},['period'],[['c08:s01','c08:s02']]),
          'segment_growth_bridge':table({'window':TEXT,'segment':TEXT,'prior_usd_million':M,'current_usd_million':M,'change_usd_million':M,'contribution_to_total_growth_pct':P},['window','segment'],[['c08:s03']])},
        'sql':{'income_reconciliation':BROADCOM_INCOME,'share_basis':BROADCOM_SHARES,'segment_growth_bridge':BROADCOM_SEGMENTS},
        'starting':{'share_basis':BROADCOM_SHARES.replace('adjusted/adjusted_shares_million','adjusted/gaap_shares_million')},
        'claims':{'semiconductor_majority_annual_growth':claim('supported',['c08:s03'],'Semiconductor solutions contributes more than half the FY2025 total-revenue increase.'),
          'gaap_denominator_matches_adjusted':claim('contradicted',['c08:s02'],'The FY2025 GAAP diluted share denominator is the matching published denominator for adjusted net income.'),
          'exact_ai_pricing_effect_identified':claim('unresolved',['c08:s03'],'The supplied segment totals separately identify the exact AI-semiconductor pricing effect.')},
        'request':'Reconcile Broadcom FY2025, both supplied Q4 periods and Q3FY2025. Rebuild signed adjusted net income, match diluted share bases and retain the effect of an incorrect GAAP denominator. Attribute annual and Q4 revenue growth by segment while separating tax, discontinued-operation and price-attribution scope.',
        'definitions':{'income_reconciliation':'Five declared periods. All net-income adjustments are signed and already expressed on the net-income reconciliation basis.',
          'share_basis':'Computed EPS uses matching million-dollar income and million-share denominators. Report the separate hypothetical adjusted-income/GAAP-share quotient and its difference from correctly based adjusted EPS.',
          'segment_growth_bridge':'Windows FY and Q4FY. Segment contribution is its dollar change divided by the matching total-revenue dollar change.'},
        'rationale':'Adjusted earnings and diluted shares both change basis. Reconciling tax and discontinued operations before matching denominators avoids an apparently plausible EPS result, while segment growth supports bounded contribution rather than a price claim.'},
      'c09':{'source':'jpm-fy2025','split':'evaluation','calculate':jpm,
        'tables':{'bank_basis_bridge':table({'period':TEXT,'managed_revenue_usd_million':M,'printed_input_reported_basis_estimate_usd_million':M,'fte_adjustment_usd_million':M,'overhead_pct':P,'adjusted_overhead_pct':P,'managed_revenue_residual_usd_million':M},['period'],[['c09:s01','c09:s03']]),
          'significant_item_bridge':table({'period':TEXT,'apple_pretax_reserve_usd_million':M,'apple_aftertax_effect_usd_million':M,'apple_tax_shield_usd_million':M,'net_income_exclusion_change_usd_million':M,'printed_input_adjusted_net_income_usd_million':M,'rounding_residual_usd_million':M},['period'],[['c09:s02']]),
          'annual_exclusion_components':table({'measure':TEXT,'signed_aftertax_exclusion_usd_million':M,'origin':TEXT},['measure'],[['c09:s02']])},
        'sql':{'bank_basis_bridge':JPM_BASIS,'significant_item_bridge':JPM_ITEMS,'annual_exclusion_components':JPM_COMPONENTS},
        'starting':{'bank_basis_bridge':JPM_BASIS.replace('(expense_usd_million-legal_expense_usd_million)/managed_revenue_usd_million','(expense_usd_million-legal_expense_usd_million)/(managed_revenue_usd_million-fte_adjustment_usd_million)')},
        'claims':{'managed_presentation_changes_net_income':claim('contradicted',['c09:s01'],'The fully taxable-equivalent managed presentation increases company net income.'),
          'annual_exclusion_less_than_q4':claim('supported',['c09:s02'],'The annual net-income exclusion increase is smaller than the Q4 increase because annual exclusions also remove gains and benefits.'),
          'exact_payment_fee_identified':claim('unresolved',['c09:s03'],'The supplied revenue and bank-basis totals identify an exact Payments processing fee.')},
        'request':'Reconcile JPMorgan FY2025 and Q4 managed presentation, adjusted overhead and significant-item exclusions. Preserve rounding residuals from printed slide inputs. Derive the implied after-tax First Republic exclusion from the disclosed combined annual change, distinguishing that derivation from a printed observation.',
        'definitions':{'bank_basis_bridge':'Reported-basis revenue is an estimate reconstructed from the rounded managed slide amounts less FTE. Overhead and adjusted overhead both use managed revenue. Retain NII plus NIR less managed-revenue residual.',
          'significant_item_bridge':'Use after-tax reserve effect for net income. The tax shield is pretax reserve less after-tax effect. Rounded disclosure residual is recomputed adjusted net income less the printed rounded adjusted total.',
          'annual_exclusion_components':'FY2025 only. Three signed after-tax exclusions sum to the disclosed annual change. Origin labels printed_after_tax and derived_after_tax distinguish directly disclosed from algebraically implied amounts.'},
        'rationale':'A bank managed basis moves revenue and tax together, while significant-item exclusion mixes pretax reserves, after-tax costs and gains. Proper denominators and a bounded derived residual must survive without inventing precise unpublished totals.'},
      'c10':{'source':'netflix-fy2025','split':'evaluation','calculate':netflix,
        'tables':{'regional_currency':table({'region':TEXT,'cc_current_usd_thousand':K,'unhedged_prior_usd_thousand':K,'reported_growth_pct':P,'cc_growth_pct':P,'currency_adjustment_usd_thousand':K,'hedging_exclusion_change_usd_thousand':K},['region'],[['c10:s01']]),
          'annual_currency_margin':table({'year':INTEGER,'operating_income_usd_thousand':K,'adjusted_operating_income_usd_thousand':K,'reported_margin_pct':P,'adjusted_margin_pct':P,'margin_change_bp':numeric('basis_points'),'residual_usd_thousand':K},['year'],[['c10:s02']]),
          'forecast_bounds':table({'year':INTEGER,'bound':TEXT,'revenue_usd_million':M,'implied_reported_revenue_growth_pct':P,'implied_operating_income_usd_million':M,'implied_operating_growth_pct':P,'included_acquisition_expense_usd_million':M},['year','bound'],[['c10:s02','c10:s03']])},
        'sql':{'regional_currency':NETFLIX_REGIONS,'annual_currency_margin':NETFLIX_MARGIN,'forecast_bounds':NETFLIX_FORECAST},
        'starting':{'forecast_bounds':NETFLIX_FORECAST.replace('f.revenue_usd_million*f.target_operating_margin_pct/100.0 implied_operating','f.revenue_usd_million*f.target_operating_margin_pct/100.0+f.included_acquisition_expense_usd_million implied_operating')},
        'claims':{'beginning_year_margin_basis_matches_regional_basis':claim('contradicted',['c10:s01','c10:s02'],'The annual margin and regional revenue reconciliations use the same currency comparison basis.'),
          'target_includes_acquisition_expense':claim('supported',['c10:s03'],'The FY2026 target operating margin already includes the stated acquisition expenses.'),
          'exact_average_member_revenue_identified':claim('unresolved',['c10:s03'],'The Q4 paid-membership milestone identifies an exact annual average-member revenue denominator.')},
        'request':'Reconcile Netflix FY2025 currency presentation with the FY2026 forecast. Preserve detailed Q4 regional precision, distinguish the annual beginning-year margin basis, and build low/high forecast implications using the reported FY2025 baseline. Assess the acquisition-expense and membership-denominator limits.',
        'definitions':{'regional_currency':'Use the detailed thousand-dollar Q4 appendix, adding signed currency and hedging-exclusion adjustments. Prior growth denominator also excludes hedging.',
          'annual_currency_margin':'Recompute revenue and expense on the beginning-year FX basis, with margin-change basis points equal to adjusted less reported margin.',
          'forecast_bounds':'FY2026 forecasts are not actuals. Implied revenue and operating growth use reported FY2025 actuals. The 31.5 percent target already includes the acquisition expense, so do not add it again.'},
        'rationale':'Quarter revenue growth and annual margin use different currency bases and precisions. A forecast bridge must match thousand-dollar actuals to million-dollar projections without double-removing an included cost or inventing average membership data.'}}

def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for r in rows:
            for f,v in r.items():
                if isinstance(v,(int,float)) and f not in ('year','reported_gaap_eps_usd','target_operating_margin_pct'):r[f]=v*2
    yield 'scaled_financials_and_matching_denominators',scaled
    changed=copy.deepcopy(data)
    if key=='c08':
        for r in changed['income_bases']:
            if r['period'] in ('FY2025','Q4FY2025'):
                r['gaap_income_usd_million']+=100
                r['reported_gaap_eps_usd']=float((D(r['gaap_income_usd_million'])/D(r['gaap_shares_million'])).quantize(D('0.01')))
        for r in changed['income_adjustments']:
            if r['period'] in ('FY2025','Q4FY2025') and r['measure']=='tax':r['signed_income_adjustment_usd_million']-=100
        yield 'gaap_tax_benefit_changes_not_adjusted_income',changed
    elif key=='c09':
        for r in changed['bank_bases']:r['fte_adjustment_usd_million']+=10
        yield 'fte_presentation_changes_reported_estimate_not_managed_ratios',changed
    else:
        for r in changed['forecasts']:r['included_acquisition_expense_usd_million']+=25
        yield 'included_forecast_cost_is_not_added_back',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        if name=='regional_q4':continue
        addition=copy.deepcopy(rows)
        for r in addition:
            if 'year' in r:r['year']+=3
            else:r['period']='FY2028'
        later[name]+=addition
    yield 'irrelevant_later_disclosures',later
