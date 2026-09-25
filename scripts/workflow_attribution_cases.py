"""Independent tax, currency and publication reconciliation contracts."""
import copy
from decimal import Decimal
from build_workflow_tasks import TEXT, INTEGER, numeric, table
from workflow_development_cases import claim
D=lambda x:Decimal(str(x))
M=numeric('usd_million',0.001)
P=numeric('percent')

def apple(data):
    index={(r['year'],r['months']):r for r in data['income'] if r['year'] in (2024,2025)}
    margins=[]
    bridges=[]
    baselines=[]
    adj={r['months']:r for r in data['prior_tax_adjustments'] if r['year']==2024}
    for (year,months),r in index.items():
        for kind in ('product','service'):
            rev,cost=D(r[kind+'_revenue_usd_million']),D(r[kind+'_cost_usd_million'])
            margins.append([year,months,kind,float(rev-cost),float(100*(rev-cost)/rev)])
    for months in (3,12):
        p,c=index[2024,months],index[2025,months]
        delta=D(c['net_income_usd_million'])-D(p['net_income_usd_million'])
        for measure in ('product_gp','service_gp','research','selling','other','tax'):
            def value(r):
                if measure.endswith('_gp'):
                    kind=measure[:-3]
                    return D(r[kind+'_revenue_usd_million'])-D(r[kind+'_cost_usd_million'])
                field={'research':'research_usd_million','selling':'selling_usd_million','other':'other_income_usd_million','tax':'tax_usd_million'}[measure]
                return D(r[field])*(1 if measure=='other' else -1)
            before,after=value(p),value(c)
            bridges.append([months,measure,float(before),float(after),float(after-before),float(100*(after-before)/delta)])
        prior=D(p['net_income_usd_million'])
        current=D(c['net_income_usd_million'])
        charge=D(adj[months]['tax_charge_usd_million'])
        baselines.append([months,float(prior),float(charge),float(prior+charge),float(current),float(100*(current/prior-1)),float(100*(current/(prior+charge)-1)),float(prior+charge-D(adj[months]['reported_adjusted_net_income_usd_million']))])
    return {'category_margin':margins,'net_income_growth_bridge':bridges,'prior_tax_baseline':baselines}

APPLE_MARGIN="""WITH p AS (SELECT year,months,'product' category,product_revenue_usd_million r,product_cost_usd_million c FROM income
UNION ALL SELECT year,months,'service',service_revenue_usd_million,service_cost_usd_million FROM income)
SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,category,r-c gross_profit_usd_million,100.0*(r-c)/r margin_pct FROM p WHERE year IN (2024,2025)"""
APPLE_BRIDGE="""WITH parts AS (SELECT year,months,'product_gp' measure,product_revenue_usd_million-product_cost_usd_million v FROM income
UNION ALL SELECT year,months,'service_gp',service_revenue_usd_million-service_cost_usd_million FROM income
UNION ALL SELECT year,months,'research',-research_usd_million FROM income
UNION ALL SELECT year,months,'selling',-selling_usd_million FROM income
UNION ALL SELECT year,months,'other',other_income_usd_million FROM income
UNION ALL SELECT year,months,'tax',-tax_usd_million FROM income)
SELECT CAST(c.months AS INTEGER) months,c.measure,p.v prior_signed_usd_million,c.v current_signed_usd_million,c.v-p.v change_usd_million,
100.0*(c.v-p.v)/(ci.net_income_usd_million-pi.net_income_usd_million) contribution_to_net_income_growth_pct
FROM parts c JOIN parts p ON c.measure=p.measure AND c.months=p.months AND c.year=2025 AND p.year=2024
JOIN income ci ON ci.year=c.year AND ci.months=c.months JOIN income pi ON pi.year=p.year AND pi.months=p.months"""
APPLE_BASELINE="""SELECT CAST(c.months AS INTEGER) months,p.net_income_usd_million prior_gaap_usd_million,a.tax_charge_usd_million,
p.net_income_usd_million+a.tax_charge_usd_million prior_adjusted_usd_million,c.net_income_usd_million current_gaap_usd_million,
100.0*(c.net_income_usd_million/p.net_income_usd_million-1) gaap_growth_pct,
100.0*(c.net_income_usd_million/(p.net_income_usd_million+a.tax_charge_usd_million)-1) current_gaap_growth_vs_adjusted_prior_pct,
p.net_income_usd_million+a.tax_charge_usd_million-a.reported_adjusted_net_income_usd_million residual_usd_million
FROM income c JOIN income p ON c.months=p.months AND c.year=2025 AND p.year=2024
JOIN prior_tax_adjustments a ON a.year=p.year AND a.months=p.months"""

def alphabet(data):
    contexts=('year_over_year','quarter_over_quarter')
    geo=[]
    bridge=[]
    hedges={r['comparison']:r for r in data['hedging'] if r['comparison'] in contexts}
    for context in contexts:
        selected=[r for r in data['geography'] if r['comparison']==context]
        for r in selected:
            p,c,f=[D(r[k]) for k in ('prior_usd_million','current_usd_million','fx_effect_usd_million')]
            cc=c-f
            geo.append([context,r['region'],float(p),float(c),float(f),float(cc),float(100*(c/p-1)),float(100*(cc/p-1))])
        prior,current,fx=[sum((D(r[k]) for r in selected),D(0)) for k in ('prior_usd_million','current_usd_million','fx_effect_usd_million')]
        h=hedges[context]
        ph,ch=D(h['prior_usd_million']),D(h['current_usd_million'])
        cc=current-fx
        ccdelta=cc-prior
        reported_delta=current+ch-prior-ph
        bridge.append([context,float(prior+ph),float(current+ch),float(cc),float(ccdelta),float(fx),float(ch-ph),float(reported_delta),float(ccdelta+fx+ch-ph-reported_delta),float(100*ccdelta/prior),float(cc-D(h['reported_cc_usd_million']))])
    components=[]
    index={(r['year'],r['measure']):D(r['revenue_usd_million']) for r in data['revenue_components'] if r['year'] in (2024,2025)}
    measures=[r['measure'] for r in data['revenue_components'] if r['year']==2025]
    delta=sum((index[2025,k]-index[2024,k] for k in measures),D(0))
    for k in measures:
        p,c=index[2024,k],index[2025,k]
        components.append([k,float(p),float(c),float(c-p),float(100*(c-p)/delta)])
    return {'geographic_currency':geo,'consolidated_currency_bridge':bridge,'revenue_growth_components':components}

ALPHABET_GEO="""SELECT comparison,region,prior_usd_million,current_usd_million,fx_effect_usd_million,current_usd_million-fx_effect_usd_million cc_current_usd_million,
100.0*(current_usd_million/prior_usd_million-1) reported_growth_pct,
100.0*((current_usd_million-fx_effect_usd_million)/prior_usd_million-1) cc_growth_pct FROM geography WHERE comparison IN ('year_over_year','quarter_over_quarter')"""
ALPHABET_BRIDGE="""WITH g AS (SELECT comparison,SUM(prior_usd_million) p,SUM(current_usd_million) c,SUM(fx_effect_usd_million) f FROM geography GROUP BY comparison)
SELECT g.comparison,p+h.prior_usd_million prior_reported_usd_million,c+h.current_usd_million current_reported_usd_million,
c-f cc_current_usd_million,c-f-p cc_change_usd_million,f fx_effect_usd_million,h.current_usd_million-h.prior_usd_million hedging_change_usd_million,
c+h.current_usd_million-p-h.prior_usd_million reported_change_usd_million,
(c-f-p)+f+(h.current_usd_million-h.prior_usd_million)-(c+h.current_usd_million-p-h.prior_usd_million) bridge_residual_usd_million,
100.0*((c-f)/p-1) cc_growth_pct,c-f-h.reported_cc_usd_million cc_disclosure_residual_usd_million FROM g JOIN hedging h ON g.comparison=h.comparison
WHERE g.comparison IN ('year_over_year','quarter_over_quarter')"""
ALPHABET_COMPONENT="""WITH total AS (SELECT SUM(CASE WHEN year=2025 THEN revenue_usd_million WHEN year=2024 THEN -revenue_usd_million ELSE 0 END) delta FROM revenue_components)
SELECT c.measure,p.revenue_usd_million prior_usd_million,c.revenue_usd_million current_usd_million,c.revenue_usd_million-p.revenue_usd_million change_usd_million,
100.0*(c.revenue_usd_million-p.revenue_usd_million)/total.delta contribution_to_reported_growth_pct FROM revenue_components c
JOIN revenue_components p ON p.measure=c.measure AND p.year=2024 AND c.year=2025 CROSS JOIN total"""

def cisco(data):
    selected=[r for r in data['income_versions'] if r['year'] in (2024,2025) and r['version'] in ('release','annual')]
    values={}
    finance=[]
    for r in selected:
        v={k:D(a) for k,a in r.items() if k not in ('year','version')}
        gp=v['product_revenue_usd_million']+v['service_revenue_usd_million']-v['product_cost_usd_million']-v['service_cost_usd_million']
        op=gp-v['operating_expense_usd_million']
        pre=op+v['other_income_usd_million']
        net=pre-v['tax_usd_million']
        values[r['version'],r['year']]=dict(v,gross_profit_usd_million=gp,operating_income_usd_million=op,pretax_usd_million=pre)
        finance.append([r['version'],r['year'],float(gp),float(op),float(pre),float(net),float(net-v['net_income_usd_million'])])
    settlement=next(r for r in data['settlement'] if r['fiscal_year_charged']==2025)
    cost,benefit=D(settlement['product_cost_charge_usd_million']),D(settlement['tax_benefit_usd_million'])
    impacts={'product_cost_usd_million':cost,'gross_profit_usd_million':-cost,'operating_income_usd_million':-cost,'pretax_usd_million':-cost,'tax_usd_million':-benefit,'net_income_usd_million':-cost+benefit}
    changes=[]
    for measure,impact in impacts.items():
        p,c=values['release',2025][measure],values['annual',2025][measure]
        changes.append([measure,float(p),float(c),float(c-p),float(impact),float(c-p-impact)])
    cash=[]
    index={(r['version'],r['measure']):D(r['amount_usd_million']) for r in data['cash_versions'] if r['year']==2025 and r['version'] in ('release','annual')}
    for measure in ('net_income','deferred_tax','inventory_change','other_asset_change','operating_cash'):
        p,c=index['release',measure],index['annual',measure]
        cash.append([measure,float(p),float(c),float(c-p)])
    return {'financial_versions':finance,'settlement_revision_bridge':changes,'cash_revision_bridge':cash}

CISCO_FINANCE="""WITH p AS (SELECT *,product_revenue_usd_million+service_revenue_usd_million-product_cost_usd_million-service_cost_usd_million gp FROM income_versions
WHERE year IN (2024,2025) AND version IN ('release','annual'))
SELECT version,CAST(year AS INTEGER) year,gp gross_profit_usd_million,gp-operating_expense_usd_million operating_income_usd_million,
gp-operating_expense_usd_million+other_income_usd_million pretax_usd_million,
gp-operating_expense_usd_million+other_income_usd_million-tax_usd_million net_income_usd_million,
gp-operating_expense_usd_million+other_income_usd_million-tax_usd_million-net_income_usd_million residual_usd_million FROM p"""
CISCO_REVISION="""WITH p AS (SELECT version,product_cost_usd_million pc,
product_revenue_usd_million+service_revenue_usd_million-product_cost_usd_million-service_cost_usd_million gp,operating_expense_usd_million e,other_income_usd_million o,tax_usd_million t,net_income_usd_million n FROM income_versions WHERE year=2025),
v AS (SELECT version,'product_cost_usd_million' measure,pc value FROM p UNION ALL SELECT version,'gross_profit_usd_million',gp FROM p
UNION ALL SELECT version,'operating_income_usd_million',gp-e FROM p UNION ALL SELECT version,'pretax_usd_million',gp-e+o FROM p
UNION ALL SELECT version,'tax_usd_million',t FROM p UNION ALL SELECT version,'net_income_usd_million',n FROM p),
b AS (SELECT a.measure,r.value prior_release_usd_million,a.value annual_report_usd_million,a.value-r.value observed_change_usd_million,
CASE WHEN a.measure='product_cost_usd_million' THEN s.product_cost_charge_usd_million WHEN a.measure='tax_usd_million' THEN -s.tax_benefit_usd_million
WHEN a.measure='net_income_usd_million' THEN -s.product_cost_charge_usd_million+s.tax_benefit_usd_million ELSE -s.product_cost_charge_usd_million END settlement_effect_usd_million
FROM v a JOIN v r ON a.measure=r.measure AND a.version='annual' AND r.version='release' CROSS JOIN settlement s WHERE s.fiscal_year_charged=2025)
SELECT *,observed_change_usd_million-settlement_effect_usd_million residual_usd_million FROM b"""
CISCO_CASH="""SELECT a.measure,r.amount_usd_million prior_release_usd_million,a.amount_usd_million annual_report_usd_million,
a.amount_usd_million-r.amount_usd_million change_usd_million FROM cash_versions a JOIN cash_versions r
ON a.measure=r.measure AND a.year=r.year AND a.version='annual' AND r.version='release' WHERE a.year=2025"""

def specifications():
    ym={'year':INTEGER,'months':INTEGER}
    return {
      'c05':{'source':'apple-fy2025','split':'evaluation','calculate':apple,
        'tables':{'category_margin':table(dict(ym,category=TEXT,gross_profit_usd_million=M,margin_pct=P),['year','months','category'],[['c05:s01']]),
          'net_income_growth_bridge':table({'months':INTEGER,'measure':TEXT,'prior_signed_usd_million':M,'current_signed_usd_million':M,'change_usd_million':M,'contribution_to_net_income_growth_pct':P},['months','measure'],[['c05:s01']]),
          'prior_tax_baseline':table({'months':INTEGER,'prior_gaap_usd_million':M,'tax_charge_usd_million':M,'prior_adjusted_usd_million':M,'current_gaap_usd_million':M,'gaap_growth_pct':P,'current_gaap_growth_vs_adjusted_prior_pct':P,'residual_usd_million':M},['months'],[['c05:s01','c05:s02']])},
        'sql':{'category_margin':APPLE_MARGIN,'net_income_growth_bridge':APPLE_BRIDGE,'prior_tax_baseline':APPLE_BASELINE},
        'starting':{'prior_tax_baseline':APPLE_BASELINE.replace('p.net_income_usd_million+a.tax_charge_usd_million','p.net_income_usd_million-a.tax_charge_usd_million')},
        'claims':{'prior_tax_charge_exceeds_half_growth':claim('supported',['c05:s01','c05:s02'],'The excluded prior tax charge exceeds half the FY2025 increase in GAAP net income.'),
          'entire_net_growth_is_operating':claim('contradicted',['c05:s01'],'The full annual GAAP net-income increase equals the operating-income increase.'),
          'exact_product_price_effect_identified':claim('unresolved',['c05:s01','c05:s03'],'The supplied category revenue and cost tables separately identify the exact product price effect.')},
        'request':'Reconcile Apple FY2025 and Q4 earnings growth across category profitability, operating expenses, signed other income and tax. Preserve both years, attribute the net-income change by component, and compare current GAAP income with both prior GAAP and the explicitly adjusted prior tax baseline.',
        'definitions':{'category_margin':'Both fiscal years, months=3 Q4 and 12 annual. Category gross margin uses category revenue.',
          'net_income_growth_bridge':'Six signed net-income components per duration. Expenses and tax enter negatively. Contributions divide by the same-duration GAAP net-income increase.',
          'prior_tax_baseline':'Remove the prior tax charge by adding it to prior net income. Current remains GAAP. Percentage growth uses each clearly declared baseline.'},
        'rationale':'A prior tax charge dominates headline net-income growth without being operating growth or a new current charge. Signed component attribution and matched category margins must coexist with a properly labeled adjusted prior comparison.'},
      'c06':{'source':'alphabet-q2fy2025','split':'evaluation','calculate':alphabet,
        'tables':{'geographic_currency':table({'comparison':TEXT,'region':TEXT,'prior_usd_million':M,'current_usd_million':M,'fx_effect_usd_million':M,'cc_current_usd_million':M,'reported_growth_pct':P,'cc_growth_pct':P},['comparison','region'],[['c06:s01']]),
          'consolidated_currency_bridge':table({'comparison':TEXT,'prior_reported_usd_million':M,'current_reported_usd_million':M,'cc_current_usd_million':M,'cc_change_usd_million':M,'fx_effect_usd_million':M,'hedging_change_usd_million':M,'reported_change_usd_million':M,'bridge_residual_usd_million':M,'cc_growth_pct':P,'cc_disclosure_residual_usd_million':M},['comparison'],[['c06:s01']]),
          'revenue_growth_components':table({'measure':TEXT,'prior_usd_million':M,'current_usd_million':M,'change_usd_million':M,'contribution_to_reported_growth_pct':P},['measure'],[['c06:s02']])},
        'sql':{'geographic_currency':ALPHABET_GEO,'consolidated_currency_bridge':ALPHABET_BRIDGE,'revenue_growth_components':ALPHABET_COMPONENT},
        'starting':{'consolidated_currency_bridge':ALPHABET_BRIDGE.replace('(c-f)/p-1','(c-f)/(p+h.prior_usd_million)-1')},
        'claims':{'prior_hedging_excluded_from_cc_growth':claim('supported',['c06:s01'],'The constant-currency growth denominator excludes prior-period hedging.'),
          'cloud_exceeds_half_reported_growth':claim('contradicted',['c06:s02'],'Google Cloud contributes more than half the reported Q2 year-over-year revenue increase.'),
          'exact_ai_product_effect_identified':claim('unresolved',['c06:s02','c06:s03'],'These revenue and currency tables separately identify the exact revenue-growth effect of AI products.')},
        'request':'Reconcile Alphabet Q2FY2025 year-over-year and sequential revenue growth. Preserve comparison-specific translation bases, separate currency from hedging, and attribute reported year-over-year growth across mutually exclusive revenue components. Assess the limit on a separate AI-product attribution.',
        'definitions':{'geographic_currency':'Two declared comparison contexts and four regions. CC current is current less that comparison FX effect.',
          'consolidated_currency_bridge':'CC growth uses prior unhedged regional revenue. Reported growth decomposes into CC change, translation FX and the change in consolidated hedging.',
          'revenue_growth_components':'Seven leaf components, including hedging. Contributions divide by total reported Q2FY2025 less Q2FY2024 revenue.'},
        'rationale':'The same current quarter has different constant-currency amounts under different comparison rates. A coherent bridge must retain that dependence and exclude prior hedging from CC growth without double-counting product subtotals.'},
      'c07':{'source':'cisco-fy2025','split':'evaluation','calculate':cisco,
        'tables':{'financial_versions':table({'version':TEXT,'year':INTEGER,'gross_profit_usd_million':M,'operating_income_usd_million':M,'pretax_usd_million':M,'net_income_usd_million':M,'residual_usd_million':M},['version','year'],[['c07:s01','c07:s02']]),
          'settlement_revision_bridge':table({'measure':TEXT,'prior_release_usd_million':M,'annual_report_usd_million':M,'observed_change_usd_million':M,'settlement_effect_usd_million':M,'residual_usd_million':M},['measure'],[['c07:s01','c07:s02']]),
          'cash_revision_bridge':table({'measure':TEXT,'prior_release_usd_million':M,'annual_report_usd_million':M,'change_usd_million':M},['measure'],[['c07:s01','c07:s03']])},
        'sql':{'financial_versions':CISCO_FINANCE,'settlement_revision_bridge':CISCO_REVISION,'cash_revision_bridge':CISCO_CASH},
        'starting':{'settlement_revision_bridge':CISCO_REVISION.replace('-s.product_cost_charge_usd_million+s.tax_benefit_usd_million','-s.product_cost_charge_usd_million-s.tax_benefit_usd_million')},
        'claims':{'annual_net_growth_direction_changes':claim('supported',['c07:s01','c07:s02'],'Annual GAAP net-income growth changes from positive in the release to negative in the superseding annual report.'),
          'settlement_requires_incremental_cash':claim('contradicted',['c07:s02'],'The disclosed product expense charge represents an equal incremental settlement cash payment.'),
          'exact_organic_revenue_growth_identified':claim('unresolved',['c07:s01','c07:s03'],'The supplied annual totals separately identify exact organic revenue growth excluding Splunk.')},
        'request':'Reconcile Cisco FY2025 as first released with the superseding annual report. Preserve FY2024, rebuild each financial version, isolate the supplier settlement charge and tax benefit, and reconcile the changed operating-cash components. Keep signatures, economic dates, publication precision and cash versus expense distinct.',
        'definitions':{'financial_versions':'Both release and annual versions for FY2024 and FY2025. Recompute gross profit, operating, pretax and net income.',
          'settlement_revision_bridge':'Six FY2025 observed changes, annual report less release, compared with the signed settlement effect. After-tax expense deducts cost and adds the tax benefit.',
          'cash_revision_bridge':'Five annual cash-flow rows. Retain all four changed reconciliation components and the unchanged reported operating-cash total.'},
        'rationale':'This is an actual subsequent-event publication conflict. Expense and tax changes reverse a headline growth direction while operating cash stays unchanged, and acquisition timing prevents exact organic attribution.'}}

def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for r in rows:
            for f,v in r.items():
                if isinstance(v,(int,float)) and f not in ('year','months','fiscal_year_charged'):r[f]=v*2
    yield 'scaled_financial_observations',scaled
    changed=copy.deepcopy(data)
    if key=='c05':
        for r in changed['income']:
            if r['year']==2024:
                r['tax_usd_million']+=100
                r['net_income_usd_million']-=100
        for r in changed['prior_tax_adjustments']:r['tax_charge_usd_million']+=100
        yield 'prior_tax_charge_changes_gaap_not_adjusted_baseline',changed
    elif key=='c06':
        for r in changed['geography']:
            if r['region']=='EMEA':
                r['current_usd_million']+=50
                r['fx_effect_usd_million']+=50
        for r in changed['revenue_components']:
            if (r['year'],r['measure'])==(2025,'Search'):r['revenue_usd_million']+=50
        yield 'currency_translation_changes_reported_not_cc',changed
    else:
        for r in changed['settlement']:
            r['product_cost_charge_usd_million']+=10
            r['tax_benefit_usd_million']+=2
        for r in changed['income_versions']:
            if (r['version'],r['year'])==('annual',2025):
                r['product_cost_usd_million']+=10
                r['tax_usd_million']-=2
                r['net_income_usd_million']-=8
        for r in changed['cash_versions']:
            if r['version']=='annual':
                r['amount_usd_million']+=dict(net_income=-8,deferred_tax=-2,other_asset_change=10).get(r['measure'],0)
        yield 'expense_and_tax_revision_preserves_total_cash',changed
    later=copy.deepcopy(data)
    if key=='c06':
        for name,rows in list(later.items()):
            addition=copy.deepcopy(rows)
            for r in addition:
                if 'year' in r:r['year']+=3
                else:r['comparison']='later_unrequested'
            later[name]+=addition
    else:
        for name,rows in list(later.items()):
            if name=='settlement':continue
            addition=copy.deepcopy(rows)
            for r in addition:r['year']+=3
            later[name]+=addition
    yield 'irrelevant_later_disclosures',later
