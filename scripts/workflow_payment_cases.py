"""Source-specific payment references and work-product contracts."""
import copy
from decimal import Decimal
from build_workflow_tasks import TEXT, numeric, table
from workflow_development_cases import claim

D=lambda x:Decimal(str(x))
M=numeric('usd_million',0.001)
B=numeric('usd_billion')
P=numeric('percent')


def robinhood(data):
    expenses=[]
    for r in data['expenses']:
        if r['period'] not in ('FY2024','FY2025','Q4FY2024','Q4FY2025','Q3FY2025'):continue
        gaap,sbc,settlement,credit,reported=[D(r[k]) for k in ('gaap_expense_usd_million','sbc_usd_million','settlement_expense_usd_million','credit_loss_exclusion_usd_million','adjusted_expense_usd_million')]
        adjusted=gaap-sbc-settlement-credit
        expenses.append([r['period'],float(gaap),float(adjusted),float(adjusted+sbc),float(-settlement),float(adjusted-reported),float(adjusted+credit-D(r['credit_loss_provision_usd_million']))])
    annual={r['period']:r for r in data['revenues'] if r['period'] in ('FY2024','FY2025')}
    p,c=annual['FY2024'],annual['FY2025']
    delta=D(c['total_usd_million'])-D(p['total_usd_million'])
    revenue=[]
    for m in ('transaction','interest','other'):
        before,after=D(p[m+'_usd_million']),D(c[m+'_usd_million'])
        revenue.append([m,float(before),float(after),float(after-before),float(100*(after-before)/delta)])
    volumes=[]
    totals={r['period']:D(r['volume_usd_billion']) for r in data['crypto_volumes'] if r['scope']=='total'}
    for r in data['crypto_volumes']:
        if r['period'] not in ('Q4FY2025','January2026') or r['scope']=='total':continue
        volume=D(r['volume_usd_billion'])
        volumes.append([r['period'],r['scope'],r['months'],float(volume),float(100*volume/totals[r['period']]),float(volume/D(r['months']))])
    return {'expense_audit':expenses,'annual_revenue_bridge':revenue,'crypto_scope':volumes}


ROBINHOOD_EXPENSE="""SELECT period,gaap_expense_usd_million,
gaap_expense_usd_million-sbc_usd_million-settlement_expense_usd_million-credit_loss_exclusion_usd_million adjusted_expense_usd_million,
gaap_expense_usd_million-settlement_expense_usd_million-credit_loss_exclusion_usd_million adjusted_including_sbc_usd_million,
-settlement_expense_usd_million removal_of_settlement_usd_million,
gaap_expense_usd_million-sbc_usd_million-settlement_expense_usd_million-credit_loss_exclusion_usd_million-adjusted_expense_usd_million residual_usd_million,
gaap_expense_usd_million-sbc_usd_million-settlement_expense_usd_million-credit_loss_provision_usd_million comparable_credit_excluded_expense_usd_million
FROM expenses WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025','Q3FY2025')"""
ROBINHOOD_REVENUE="""WITH p AS (SELECT * FROM revenues WHERE period='FY2024'),c AS (SELECT * FROM revenues WHERE period='FY2025'),
components AS (SELECT 'transaction' measure,p.transaction_usd_million prior,c.transaction_usd_million current FROM p CROSS JOIN c
UNION ALL SELECT 'interest',p.interest_usd_million,c.interest_usd_million FROM p CROSS JOIN c
UNION ALL SELECT 'other',p.other_usd_million,c.other_usd_million FROM p CROSS JOIN c)
SELECT measure,prior prior_usd_million,current current_usd_million,current-prior change_usd_million,
100.0*(current-prior)/(c.total_usd_million-p.total_usd_million) contribution_to_total_growth_pct FROM components CROSS JOIN p CROSS JOIN c"""
ROBINHOOD_CRYPTO="""SELECT s.period,s.scope,CAST(s.months AS INTEGER) months,s.volume_usd_billion,
100.0*s.volume_usd_billion/t.volume_usd_billion share_of_combined_pct,
1.0*s.volume_usd_billion/s.months monthly_average_usd_billion FROM crypto_volumes s JOIN crypto_volumes t ON t.period=s.period AND t.scope='total'
WHERE s.period IN ('Q4FY2025','January2026') AND s.scope IN ('app','bitstamp')"""


def visa(data):
    facts={(r['period'],r['measure']):D(r['amount_usd_million']) for r in data['revenue_components']}
    revenue=[]
    for p in ('FY2025','Q4FY2025','9MFY2025'):
        def f(m):return facts['FY2025',m]-facts['Q4FY2025',m] if p=='9MFY2025' else facts[p,m]
        gross=sum((f(m) for m in ('service','data_processing','international','other')),D(0))
        incentives=f('client_incentives')
        net=gross+incentives
        revenue.append([p,float(gross),float(incentives),float(net),float(100*-incentives/gross),float(net-f('net_revenue'))])
    net_income=[]
    groups={p:[r for r in data['net_income_reconciliation'] if r['period']==p] for p in ('FY2024','FY2025','Q4FY2024','Q4FY2025')}
    values={}
    for p,rows in groups.items():
        gaap=next(D(r['amount_usd_million']) for r in rows if r['measure']=='gaap')
        reported=next(D(r['amount_usd_million']) for r in rows if r['measure']=='adjusted')
        changes=sum((D(r['amount_usd_million']) for r in rows if r['measure'] not in ('gaap','adjusted')),D(0))
        litigation=sum((D(r['amount_usd_million']) for r in rows if r['measure']=='litigation'),D(0))
        net_income.append([p,float(gaap),float(changes),float(gaap+changes),float(litigation),float(gaap+changes-reported)])
        values[p]=(gaap,reported)
    growth=[]
    for w in ('FY','Q4FY'):
        gaap_p,adj_p=values[w+'2024']
        gaap_c,adj_c=values[w+'2025']
        growth.append([w,float(gaap_c-gaap_p),float(adj_c-adj_p),float(100*(gaap_c/gaap_p-1)),float(100*(adj_c/adj_p-1)),float((adj_c-gaap_c)-(adj_p-gaap_p))])
    return {'gross_to_net':revenue,'net_income_reconciliation':net_income,'income_growth_bridge':growth}


VISA_REVENUE="""WITH p AS (SELECT period,
SUM(CASE WHEN measure IN ('service','data_processing','international','other') THEN amount_usd_million ELSE 0 END) g,
MAX(CASE WHEN measure='client_incentives' THEN amount_usd_million END) i,
MAX(CASE WHEN measure='net_revenue' THEN amount_usd_million END) n FROM revenue_components WHERE period IN ('FY2025','Q4FY2025') GROUP BY period),
periods AS (SELECT * FROM p UNION ALL SELECT '9MFY2025',a.g-q.g,a.i-q.i,a.n-q.n FROM p a JOIN p q ON a.period='FY2025' AND q.period='Q4FY2025')
SELECT period,g gross_revenue_usd_million,i incentives_usd_million,g+i net_revenue_usd_million,-100.0*i/g incentive_share_of_gross_pct,g+i-n residual_usd_million FROM periods"""
VISA_INCOME="""WITH p AS (SELECT period,MAX(CASE WHEN measure='gaap' THEN amount_usd_million END) g,
MAX(CASE WHEN measure='adjusted' THEN amount_usd_million END) reported,
SUM(CASE WHEN measure NOT IN ('gaap','adjusted') THEN amount_usd_million ELSE 0 END) a,
SUM(CASE WHEN measure='litigation' THEN amount_usd_million ELSE 0 END) l
FROM net_income_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT period,g gaap_income_usd_million,a after_tax_adjustments_usd_million,g+a adjusted_income_usd_million,l litigation_adjustment_usd_million,g+a-reported residual_usd_million FROM p"""
VISA_GROWTH="""WITH p AS (SELECT period,MAX(CASE WHEN measure='gaap' THEN amount_usd_million END) g,
MAX(CASE WHEN measure='adjusted' THEN amount_usd_million END) a FROM net_income_reconciliation GROUP BY period)
SELECT CASE WHEN c.period='FY2025' THEN 'FY' ELSE 'Q4FY' END window,c.g-p.g gaap_change_usd_million,c.a-p.a adjusted_change_usd_million,
100.0*(c.g/p.g-1) gaap_growth_pct,100.0*(c.a/p.a-1) adjusted_growth_pct,(c.a-c.g)-(p.a-p.g) gap_change_usd_million
FROM p c JOIN p p ON (c.period='FY2025' AND p.period='FY2024') OR (c.period='Q4FY2025' AND p.period='Q4FY2024')"""


def mastercard(data):
    regions={(r['period'],r['region']):r for r in data['regions']}
    worldwide={r['period']:r for r in data['worldwide']}
    attribution=[]
    for window in ('FY','Q4FY'):
        total_delta=D(worldwide[window+'2025']['purchase_usd_billion'])-D(worldwide[window+'2024']['purchase_usd_billion'])
        for region in ('APMEA','Canada','Europe','Latin America','United States'):
            p,c=regions[window+'2024',region],regions[window+'2025',region]
            pv,cv=D(p['purchase_usd_billion']),D(c['purchase_usd_billion'])
            pa=1000*pv/D(p['purchase_transactions_million'])
            ca=1000*cv/D(c['purchase_transactions_million'])
            attribution.append([window,region,float(pv),float(cv),float(cv-pv),float(100*(cv-pv)/total_delta),float(pa),float(ca),float(100*(ca/pa-1)),float(D(c['purchase_usd_billion'])+D(c['cash_usd_billion'])-D(c['gdv_usd_billion']))])
    reconciliation=[]
    for period in ('FY2024','FY2025','Q4FY2024','Q4FY2025'):
        rows=[r for r in data['regions'] if r['period']==period]
        sums=[sum((D(r[k]) for r in rows),D(0)) for k in ('gdv_usd_billion','purchase_usd_billion','purchase_transactions_million')]
        residual=[s-D(worldwide[period][k]) for s,k in zip(sums,('gdv_usd_billion','purchase_usd_billion','purchase_transactions_million'))]
        reconciliation.append([period,*map(float,sums),*map(float,residual)])
    financial=[]
    for r in data['financials']:
        if r['period'] not in ('FY2024','FY2025','Q4FY2024','Q4FY2025'):continue
        revenue,gaap,litigation,restructuring,reported=[D(r[k]) for k in ('revenue_usd_million','gaap_expense_usd_million','litigation_usd_million','restructuring_usd_million','adjusted_expense_usd_million')]
        reconstructed=gaap-litigation-restructuring
        financial.append([r['period'],float(revenue-gaap),float(revenue-reported),float(100*(revenue-gaap)/revenue),float(100*(revenue-reported)/revenue),float(reconstructed-reported)])
    return {'regional_attribution':attribution,'worldwide_reconciliation':reconciliation,'company_margin_bridge':financial}


MA_ATTRIBUTION="""SELECT CASE WHEN c.period='FY2025' THEN 'FY' ELSE 'Q4FY' END window,c.region,
p.purchase_usd_billion prior_purchase_usd_billion,c.purchase_usd_billion current_purchase_usd_billion,
c.purchase_usd_billion-p.purchase_usd_billion change_usd_billion,
100.0*(c.purchase_usd_billion-p.purchase_usd_billion)/(wc.purchase_usd_billion-wp.purchase_usd_billion) contribution_to_worldwide_purchase_growth_pct,
1000.0*p.purchase_usd_billion/p.purchase_transactions_million prior_average_purchase_usd,
1000.0*c.purchase_usd_billion/c.purchase_transactions_million current_average_purchase_usd,
100.0*((c.purchase_usd_billion/c.purchase_transactions_million)/(p.purchase_usd_billion/p.purchase_transactions_million)-1) average_purchase_growth_pct,
c.purchase_usd_billion+c.cash_usd_billion-c.gdv_usd_billion current_gdv_residual_usd_billion
FROM regions c JOIN regions p ON c.region=p.region AND ((c.period='FY2025' AND p.period='FY2024') OR (c.period='Q4FY2025' AND p.period='Q4FY2024'))
JOIN worldwide wc ON wc.period=c.period JOIN worldwide wp ON wp.period=p.period"""
MA_RECON="""WITH p AS (SELECT period,SUM(gdv_usd_billion) g,SUM(purchase_usd_billion) v,SUM(purchase_transactions_million) n
FROM regions WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT p.period,g regional_gdv_usd_billion,v regional_purchase_usd_billion,n regional_purchase_transactions_million,
g-w.gdv_usd_billion gdv_residual_usd_billion,v-w.purchase_usd_billion purchase_residual_usd_billion,
n-w.purchase_transactions_million transaction_residual_million FROM p JOIN worldwide w USING(period)"""
MA_MARGIN="""SELECT period,revenue_usd_million-gaap_expense_usd_million gaap_operating_income_usd_million,
revenue_usd_million-adjusted_expense_usd_million adjusted_operating_income_usd_million,
100.0*(revenue_usd_million-gaap_expense_usd_million)/revenue_usd_million gaap_margin_pct,
100.0*(revenue_usd_million-adjusted_expense_usd_million)/revenue_usd_million adjusted_margin_pct,
gaap_expense_usd_million-litigation_usd_million-restructuring_usd_million-adjusted_expense_usd_million expense_residual_usd_million
FROM financials WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025')"""


def specifications():
    return {
      'b04':{'source':'robinhood-fy2025','split':'evaluation','calculate':robinhood,'starting_defects':'Authored reviewed work product, no injected SQL defect, no-change is a valid outcome',
        'tables':{
          'expense_audit':table({'period':TEXT,'gaap_expense_usd_million':M,'adjusted_expense_usd_million':M,'adjusted_including_sbc_usd_million':M,'removal_of_settlement_usd_million':M,'residual_usd_million':M,'comparable_credit_excluded_expense_usd_million':M},['period'],[['b04:s01']]),
          'annual_revenue_bridge':table({'measure':TEXT,'prior_usd_million':M,'current_usd_million':M,'change_usd_million':M,'contribution_to_total_growth_pct':P},['measure'],[['b04:s01']]),
          'crypto_scope':table({'period':TEXT,'scope':TEXT,'months':{'type':'integer','unit':'count'},'volume_usd_billion':B,'share_of_combined_pct':P,'monthly_average_usd_billion':B},['period','scope'],[['b04:s02']])},
        'sql':{'expense_audit':ROBINHOOD_EXPENSE,'annual_revenue_bridge':ROBINHOOD_REVENUE,'crypto_scope':ROBINHOOD_CRYPTO},
        'claims':{'bitstamp_majority_q4':claim('supported',['b04:s02'],'Bitstamp represents more than half of Q4FY2025 combined crypto notional volume.'),
          'removing_settlement_benefit_reduces_expense':claim('contradicted',['b04:s01'],'Removing the Q4FY2024 settlement benefit lowers adjusted operating expense.'),
          'organic_asset_gain_identified':claim('unresolved',['b04:s03'],'The supplied observations identify the exact FY2025 organic investment return within Total Platform Assets.')},
        'request':'Audit the Robinhood FY2025 research project without assuming a repair is required. Retain valid SQL and document any identifiable defects. Reconcile adjusted expenses, including negative prior settlement amounts and both the reported and a consistently credit-excluded expense basis. Attribute annual revenue growth across transaction, interest and other revenue. Separate app and Bitstamp crypto volume in Q4 and preliminary January, normalizing duration only as a monthly arithmetic average. Resolve the scope of any organic asset-growth inference.',
        'definitions':{'expense_audit':'Adjusted expense subtracts signed SBC, settlements and credit losses. Including SBC adds it back to adjusted expense. Settlement removal is minus the signed settlement expense.',
          'annual_revenue_bridge':'Use reported annual component changes divided by reported total revenue change.',
          'crypto_scope':'Two output scopes, app and bitstamp, for Q4FY2025 and January2026. Share uses the combined total for that same period. Monthly average divides by disclosed duration and is not a seasonally adjusted forecast.'},
        'rationale':'A valid work product should survive an audit. Negative settlements and a changed expense exclusion create plausible but unnecessary edits. Acquired crypto volume and a preliminary month require scope and duration discipline, while acquired assets prevent an unsupported organic-return story.'},
      'c03':{'source':'visa-fy2025','split':'evaluation','calculate':visa,
        'tables':{
          'gross_to_net':table({'period':TEXT,'gross_revenue_usd_million':M,'incentives_usd_million':M,'net_revenue_usd_million':M,'incentive_share_of_gross_pct':P,'residual_usd_million':M},['period'],[['c03:s01']]),
          'net_income_reconciliation':table({'period':TEXT,'gaap_income_usd_million':M,'after_tax_adjustments_usd_million':M,'adjusted_income_usd_million':M,'litigation_adjustment_usd_million':M,'residual_usd_million':M},['period'],[['c03:s02']]),
          'income_growth_bridge':table({'window':TEXT,'gaap_change_usd_million':M,'adjusted_change_usd_million':M,'gaap_growth_pct':P,'adjusted_growth_pct':P,'gap_change_usd_million':M},['window'],[['c03:s02']])},
        'sql':{'gross_to_net':VISA_REVENUE,'net_income_reconciliation':VISA_INCOME,'income_growth_bridge':VISA_GROWTH},
        'starting':{'gross_to_net':VISA_REVENUE.replace('g+i net_revenue','g-i net_revenue')},
        'claims':{'q4_gaap_and_adjusted_same_direction':claim('contradicted',['c03:s02'],'Q4FY2025 GAAP and adjusted net income both grew relative to Q4FY2024.'),
          'litigation_majority_annual_gap':claim('supported',['c03:s02'],'Litigation accounts for more than half the FY2025 adjusted-minus-GAAP net-income gap.'),
          'same_quarter_price_effect_identified':claim('unresolved',['c03:s03'],'The supplied same-quarter volume growth identifies the exact pricing contribution to service revenue growth.')},
        'request':'Reconcile Visa FY2025 revenue and earnings before attributing operating improvement. Build the current annual, Q4 and reconstructed nine-month gross-to-net bridge, preserving signed client incentives. Reconcile after-tax net-income adjustments for both years and both Q4 comparisons, then show how GAAP and adjusted growth diverge. Distinguish litigation exclusions from recurring revenue economics and respect service-revenue timing.',
        'definitions':{'gross_to_net':'FY2025, Q4FY2025 and 9MFY2025. Gross sums four positive revenue categories, incentives keep their negative source sign. First nine months is annual less Q4.',
          'net_income_reconciliation':'Use the net-income column of each reconciliation, already after tax. Missing categories are not separately observed adjustments.',
          'income_growth_bridge':'Windows FY and Q4FY compare FY2025 with FY2024. Gap change is current adjusted-minus-GAAP gap less prior gap.'},
        'rationale':'A net revenue bridge and an after-tax earnings bridge answer different questions. Signed incentives, cumulative periods and legal exclusions interact, while the lagged service-volume basis prevents a causal pricing attribution from the headline growth rates.'},
      'c04':{'source':'mastercard-fy2025','split':'evaluation','calculate':mastercard,
        'tables':{
          'regional_attribution':table({'window':TEXT,'region':TEXT,'prior_purchase_usd_billion':B,'current_purchase_usd_billion':B,'change_usd_billion':B,'contribution_to_worldwide_purchase_growth_pct':P,'prior_average_purchase_usd':numeric('usd'),'current_average_purchase_usd':numeric('usd'),'average_purchase_growth_pct':P,'current_gdv_residual_usd_billion':B},['window','region'],[['c04:s01','c04:s02']]),
          'worldwide_reconciliation':table({'period':TEXT,'regional_gdv_usd_billion':B,'regional_purchase_usd_billion':B,'regional_purchase_transactions_million':numeric('million_transactions'),'gdv_residual_usd_billion':B,'purchase_residual_usd_billion':B,'transaction_residual_million':numeric('million_transactions')},['period'],[['c04:s01']]),
          'company_margin_bridge':table({'period':TEXT,'gaap_operating_income_usd_million':M,'adjusted_operating_income_usd_million':M,'gaap_margin_pct':P,'adjusted_margin_pct':P,'expense_residual_usd_million':M},['period'],[['c04:s03']])},
        'sql':{'regional_attribution':MA_ATTRIBUTION,'worldwide_reconciliation':MA_RECON,'company_margin_bridge':MA_MARGIN},
        'starting':{'regional_attribution':MA_ATTRIBUTION.replace('1000.0*p.purchase','1.0*p.purchase').replace('1000.0*c.purchase','1.0*c.purchase')},
        'claims':{'branded_volume_matches_all_revenue':claim('contradicted',['c04:s02','c04:s03'],'Branded purchase volume and total company net revenue have identical scope.'),
          'annual_average_purchase_increased':claim('supported',['c04:s01','c04:s02'],'Worldwide annual average purchase value per branded purchase transaction increased from FY2024 to FY2025.'),
          'merchant_price_mix_identified':claim('unresolved',['c04:s02'],'The supplied operational tables separately identify merchant price changes and customer basket-mix effects.')},
        'request':'Produce a Mastercard FY2025 attribution workpaper using the branded operational tables and company financial reconciliations. Attribute annual and Q4 worldwide purchase-volume growth to five mutually exclusive regions, compare average purchase sizes, and reconcile regional totals with worldwide rows. Preserve source-rounding residuals and avoid adding subtotal or credit/debit partitions twice. Reconcile company operating margins separately from the operational measures.',
        'definitions':{'regional_attribution':'FY and Q4FY windows compare 2025 to 2024. Regions are APMEA, Canada, Europe, Latin America and United States. Contribution divides regional purchase-volume change by reported worldwide purchase-volume change. Average purchase is purchase dollars per purchase transaction.',
          'worldwide_reconciliation':'Four original periods. Residuals are sums of the five exclusive regional rows less reported worldwide amounts.',
          'company_margin_bridge':'Use reported adjusted operating expense to calculate adjusted income/margin. Expense residual is GAAP less listed litigation/restructuring exclusions less reported adjusted expense, retaining the source rounding remainder.'},
        'rationale':'Branded operational tables contain overlapping subtotals and program partitions. A usable attribution must preserve their hierarchy, billion/million unit conversion and rounding. Company revenue has wider scope, so purchase-size changes cannot be read as network pricing or independently separated merchant price and mix effects.'}}


def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for row in rows:
            for field,value in row.items():
                if isinstance(value,(int,float)) and field!='months':row[field]=value*2
    yield 'scaled_amounts_preserve_ratios',scaled
    changed=copy.deepcopy(data)
    if key=='b04':
        for r in changed['expenses']:
            if r['period'] in ('FY2025','Q4FY2025'):
                r['credit_loss_exclusion_usd_million']+=10
                r['credit_loss_provision_usd_million']+=10
                r['gaap_expense_usd_million']+=10
        yield 'credit_loss_changes_gaap_not_adjusted',changed
    elif key=='c03':
        for r in changed['revenue_components']:
            if r['period'] in ('FY2025','Q4FY2025'):
                if r['measure']=='service':r['amount_usd_million']+=100
                if r['measure']=='client_incentives':r['amount_usd_million']-=100
        yield 'gross_and_incentive_increase_net_unchanged',changed
    else:
        for r in changed['regions']:
            if r['period'] in ('FY2025','Q4FY2025'):
                if r['region']=='Europe':
                    r['purchase_usd_billion']+=10
                    r['gdv_usd_billion']+=10
                if r['region']=='United States':
                    r['purchase_usd_billion']-=10
                    r['gdv_usd_billion']-=10
        yield 'regional_mix_changes_worldwide_unchanged',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        added=copy.deepcopy(rows)
        for r in added:r['period']=r['period'].replace('2025','2027').replace('2024','2028').replace('January2026','January2029')
        later[name]+=added
    yield 'irrelevant_later_disclosures',later
