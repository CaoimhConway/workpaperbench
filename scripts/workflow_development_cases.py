"""Independent references and authored work products for three new development cases."""
import copy
from datetime import date
from decimal import Decimal

from build_workflow_tasks import INTEGER, TEXT, numeric, table

D = lambda value: Decimal(str(value))
MONEY = numeric('usd_million')
USD = numeric('usd', 0.001)
PERCENT = numeric('percent')


def meta_reference(data):
    cash = {(r['fiscal_year'],r['months'],r['measure']):D(r['amount']) for r in data['cashflows']}
    segments = {(r['fiscal_year'],r['months'],r['segment'],r['measure']):D(r['amount']) for r in data['segments']}
    model, bridge, segment_model = [], [], []
    noncash = ['Depreciation and amortization','Share-based compensation','Deferred income taxes',
               'Unrealized (gain) loss on equity investments','Impairment charges for facilities consolidation','Other']
    working = ['Accounts receivable','Prepaid expenses and other current assets','Other assets','Accounts payable',
               'Accrued expenses and other current liabilities','Other liabilities']
    for year in (2024,2025):
        def flow(months,measure):
            return cash[year,12,measure]-cash[year,3,measure] if months==9 else cash[year,months,measure]
        for months in (3,9,12):
            net, operating = flow(months,'Net income'),flow(months,'Net cash provided by operating activities')
            property_out = -flow(months,'Purchases of property and equipment')
            leases = -flow(months,'Principal payments on finance leases')
            fcf = operating-property_out-leases
            model.append([year,months,float(net),float(operating),float(property_out),float(leases),float(fcf),float(fcf-net)])
            noncash_amount = sum((flow(months,label) for label in noncash),D(0))
            working_amount = sum((flow(months,label) for label in working),D(0))
            bridge.append([year,months,float(noncash_amount),float(working_amount),float(net+noncash_amount+working_amount-operating)])
            for segment in ('Family of Apps','Reality Labs'):
                def amount(measure):
                    return segments[year,12,segment,measure]-segments[year,3,segment,measure] if months==9 else segments[year,months,segment,measure]
                revenue,income = amount('revenue'),amount('operating_income')
                segment_model.append([year,months,segment,float(revenue),float(income),float(100*income/revenue)])
    return {'cash_model':model,'operating_cash_bridge':bridge,'segment_model':segment_model}


META_CASH_SQL = """WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net income' THEN amount END) ni,
MAX(CASE WHEN measure='Net cash provided by operating activities' THEN amount END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount END) pp,
-MAX(CASE WHEN measure='Principal payments on finance leases' THEN amount END) lease
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ni-q.ni,a.ocf-q.ocf,a.pp-q.pp,a.lease-q.lease
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,ni net_income_usd_million,ocf operating_cash_usd_million,
pp property_spending_usd_million,lease lease_principal_usd_million,ocf-pp-lease free_cash_flow_usd_million,
ocf-pp-lease-ni fcf_less_net_income_usd_million FROM periods"""
META_BRIDGE_SQL = """WITH p AS (SELECT fiscal_year,months,
SUM(CASE WHEN measure IN ('Depreciation and amortization','Share-based compensation','Deferred income taxes',
'Unrealized (gain) loss on equity investments','Impairment charges for facilities consolidation','Other') THEN amount ELSE 0 END) nc,
SUM(CASE WHEN measure IN ('Accounts receivable','Prepaid expenses and other current assets','Other assets','Accounts payable',
'Accrued expenses and other current liabilities','Other liabilities') THEN amount ELSE 0 END) wc,
MAX(CASE WHEN measure='Net income' THEN amount END) ni,
MAX(CASE WHEN measure='Net cash provided by operating activities' THEN amount END) ocf
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.nc-q.nc,a.wc-q.wc,a.ni-q.ni,a.ocf-q.ocf
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,nc noncash_adjustments_usd_million,wc working_capital_change_usd_million,
ni+nc+wc-ocf residual_usd_million FROM periods"""
META_SEGMENT_SQL = """WITH p AS (SELECT fiscal_year,months,segment,
MAX(CASE WHEN measure='revenue' THEN amount END) r,
MAX(CASE WHEN measure='operating_income' THEN amount END) oi
FROM segments WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months,segment),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.segment,a.r-q.r,a.oi-q.oi
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.segment=q.segment WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,segment,r revenue_usd_million,oi operating_income_usd_million,
100.0*oi/r operating_margin_pct FROM periods"""


def paxos_reference(data):
    coverage, valuations, bridges = [], [], []
    by_date = {r['economic_date']:r for r in data['reserve_observations']}
    holdings = {(r['economic_date'],r['cusip']):r for r in data['treasury_holdings']}
    for observed in ('2026-01-30','2026-02-10','2026-02-27'):
        row=by_date[observed]
        bills=[r for (d,_),r in holdings.items() if d==observed]
        par,cost,fair=[sum((D(r[field]) for r in bills),D(0)) for field in ('par_usd','cost_usd','fair_value_usd')]
        assets=D(row['cash_usd'])+D(row['repo_fair_value_usd'])+fair
        tokens=D(row['redeemable_tokens'])
        coverage.append([observed,float(assets),row['redeemable_tokens'],float(100*assets/tokens),
                         float(assets-tokens),float(assets-D(row['reported_assets_usd'])),
                         (date.fromisoformat(row['signature_date'])-date.fromisoformat(observed)).days])
        valuations.append([observed,len(bills),float(par),float(cost),float(fair),float(fair-cost),float(fair-par),float(fair-D(row['treasury_fair_value_usd']))])
    for prior,current in (('2026-01-30','2026-02-10'),('2026-02-10','2026-02-27')):
        p,c=by_date[prior],by_date[current]
        changes=[D(c[k])-D(p[k]) for k in ('cash_usd','repo_fair_value_usd','treasury_fair_value_usd')]
        delta_tokens=c['redeemable_tokens']-p['redeemable_tokens']
        asset_delta=sum(changes,D(0))
        bridges.append([prior,current,*map(float,changes),float(asset_delta),delta_tokens,float(asset_delta-D(delta_tokens))])
    return {'qualified_coverage':coverage,'treasury_valuation':valuations,'stock_bridge':bridges}


PAXOS_VALUATION_CTE = """WITH holdings AS (SELECT DISTINCT * FROM treasury_holdings),t AS (
SELECT economic_date,COUNT(*) n,SUM(par_usd) par,SUM(cost_usd) cost,SUM(fair_value_usd) fv
FROM holdings GROUP BY economic_date) """
PAXOS_COVERAGE_SQL=PAXOS_VALUATION_CTE+"""SELECT o.economic_date,o.cash_usd+o.repo_fair_value_usd+t.fv assets_usd,
o.redeemable_tokens,100.0*(o.cash_usd+o.repo_fair_value_usd+t.fv)/o.redeemable_tokens coverage_pct,
o.cash_usd+o.repo_fair_value_usd+t.fv-o.redeemable_tokens surplus_usd,
o.cash_usd+o.repo_fair_value_usd+t.fv-o.reported_assets_usd residual_usd,
CAST(julianday(o.signature_date)-julianday(o.economic_date) AS INTEGER) days_to_signature
FROM reserve_observations o JOIN t USING(economic_date)
WHERE o.economic_date IN ('2026-01-30','2026-02-10','2026-02-27')"""
PAXOS_TREASURY_SQL=PAXOS_VALUATION_CTE+"""SELECT o.economic_date,t.n distinct_holdings,t.par par_usd,t.cost cost_usd,t.fv fair_value_usd,
t.fv-t.cost valuation_gain_usd,t.fv-t.par discount_to_par_usd,t.fv-o.treasury_fair_value_usd residual_usd
FROM reserve_observations o JOIN t USING(economic_date)
WHERE o.economic_date IN ('2026-01-30','2026-02-10','2026-02-27')"""
PAXOS_BRIDGE_SQL="""SELECT p.economic_date prior_date,c.economic_date current_date,
c.cash_usd-p.cash_usd cash_change_usd,c.repo_fair_value_usd-p.repo_fair_value_usd repo_change_usd,
c.treasury_fair_value_usd-p.treasury_fair_value_usd treasury_change_usd,
c.reported_assets_usd-p.reported_assets_usd asset_change_usd,c.redeemable_tokens-p.redeemable_tokens token_change,
(c.reported_assets_usd-c.redeemable_tokens)-(p.reported_assets_usd-p.redeemable_tokens) surplus_change_usd
FROM reserve_observations p JOIN reserve_observations c ON
(p.economic_date='2026-01-30' AND c.economic_date='2026-02-10') OR
(p.economic_date='2026-02-10' AND c.economic_date='2026-02-27')"""


def adobe_reference(data):
    facts={(r['period'],r['measure']):D(r['amount']) for r in data['operating_reconciliation']}
    adjustments=['stock_based_deferred_compensation','amortization','acquisition_expense','loss_contingency_reversal','lease_impairment']
    recon=[]
    for period in ('FY2024','FY2025','Q4FY2024','Q3FY2025','Q4FY2025'):
        gaap,adjusted=facts[period,'gaap_operating_income'],facts[period,'non_gaap_operating_income']
        gap=sum((facts[period,m] for m in adjustments),D(0))
        recon.append([period,float(gaap),float(gap),float(adjusted),float(gaap+gap-adjusted)])
    prior_gap=facts['FY2024','non_gaap_operating_income']-facts['FY2024','gaap_operating_income']
    current_gap=facts['FY2025','non_gaap_operating_income']-facts['FY2025','gaap_operating_income']
    attribution=[]
    for measure in adjustments:
        p,c=facts['FY2024',measure],facts['FY2025',measure]
        attribution.append([measure,float(p),float(c),float(c-p),float(100*(c-p)/(current_gap-prior_gap))])
    arr={r['basis']:D(r['amount_usd_billion']) for r in data['arr_basis']}
    growth=next(D(r['value']) for r in data['targets'] if r['measure']=='ending_arr_growth_pct')
    before,after=arr['FY2025_exit'],arr['FY2026_opening_revalued']
    return {'operating_reconciliation':recon,'adjustment_attribution':attribution,
            'arr_guidance_bridge':[['FY2026',float(before),float(after),float(1000*(after-before)),float(growth),float(after*(1+growth/100))]]}


ADOBE_RECON_SQL="""WITH p AS (SELECT period,
MAX(CASE WHEN measure='gaap_operating_income' THEN amount END) gaap,
MAX(CASE WHEN measure='non_gaap_operating_income' THEN amount END) adjusted,
SUM(CASE WHEN measure NOT IN ('gaap_operating_income','non_gaap_operating_income') THEN amount ELSE 0 END) gap
FROM operating_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q3FY2025','Q4FY2025') GROUP BY period)
SELECT period,gaap gaap_operating_income_usd_million,gap adjustments_usd_million,
adjusted adjusted_operating_income_usd_million,gaap+gap-adjusted residual_usd_million FROM p"""
ADOBE_ATTRIBUTION_SQL="""WITH p AS (SELECT measure,
MAX(CASE WHEN period='FY2024' THEN amount END) prior,
MAX(CASE WHEN period='FY2025' THEN amount END) current
FROM operating_reconciliation WHERE period IN ('FY2024','FY2025') GROUP BY measure),
t AS (SELECT (SELECT current-prior FROM p WHERE measure='non_gaap_operating_income')-
(SELECT current-prior FROM p WHERE measure='gaap_operating_income') gap_delta)
SELECT measure,prior prior_usd_million,current current_usd_million,current-prior change_usd_million,
100.0*(current-prior)/t.gap_delta contribution_to_gap_change_pct FROM p CROSS JOIN t
WHERE measure NOT IN ('gaap_operating_income','non_gaap_operating_income')"""
ADOBE_ARR_SQL="""SELECT 'FY2026' fiscal_year,p.amount_usd_billion observed_exit_arr_usd_billion,
c.amount_usd_billion revalued_opening_arr_usd_billion,
1000.0*(c.amount_usd_billion-p.amount_usd_billion) revaluation_usd_million,
t.value target_arr_growth_pct,c.amount_usd_billion*(1+t.value/100.0) implied_target_arr_usd_billion
FROM arr_basis p CROSS JOIN arr_basis c JOIN targets t ON t.period='FY2026' AND t.measure='ending_arr_growth_pct'
WHERE p.basis='FY2025_exit' AND c.basis='FY2026_opening_revalued'"""


def claim(verdict,evidence,assertion):
    return {'verdict':verdict,'evidence':[evidence],'assertion':assertion}


def specifications():
    periods={'fiscal_year':INTEGER,'months':INTEGER}
    cash_tables={
      'cash_model':table(dict(periods,net_income_usd_million=MONEY,operating_cash_usd_million=MONEY,property_spending_usd_million=MONEY,
         lease_principal_usd_million=MONEY,free_cash_flow_usd_million=MONEY,fcf_less_net_income_usd_million=MONEY),['fiscal_year','months'],[['a02:s01','a02:s03']]),
      'operating_cash_bridge':table(dict(periods,noncash_adjustments_usd_million=MONEY,working_capital_change_usd_million=MONEY,residual_usd_million=MONEY),['fiscal_year','months'],[['a02:s01']]),
      'segment_model':table(dict(periods,segment=TEXT,revenue_usd_million=MONEY,operating_income_usd_million=MONEY,operating_margin_pct=PERCENT),['fiscal_year','months','segment'],[['a02:s02']])}
    paxos_tables={
      'qualified_coverage':table({'economic_date':TEXT,'assets_usd':USD,'redeemable_tokens':INTEGER,'coverage_pct':PERCENT,'surplus_usd':USD,'residual_usd':USD,'days_to_signature':INTEGER},['economic_date'],[['b02:s01','b02:s02','b02:s05']]),
      'treasury_valuation':table({'economic_date':TEXT,'distinct_holdings':INTEGER,'par_usd':USD,'cost_usd':USD,'fair_value_usd':USD,'valuation_gain_usd':USD,'discount_to_par_usd':USD,'residual_usd':USD},['economic_date'],[['b02:s01','b02:s02','b02:s05']]),
      'stock_bridge':table({'prior_date':TEXT,'current_date':TEXT,'cash_change_usd':USD,'repo_change_usd':USD,'treasury_change_usd':USD,'asset_change_usd':USD,'token_change':INTEGER,'surplus_change_usd':USD},['prior_date','current_date'],[['b02:s01','b02:s02']])}
    adobe_tables={
      'operating_reconciliation':table({'period':TEXT,'gaap_operating_income_usd_million':MONEY,'adjustments_usd_million':MONEY,'adjusted_operating_income_usd_million':MONEY,'residual_usd_million':MONEY},['period'],[['c02:s01']]),
      'adjustment_attribution':table({'measure':TEXT,'prior_usd_million':MONEY,'current_usd_million':MONEY,'change_usd_million':MONEY,'contribution_to_gap_change_pct':PERCENT},['measure'],[['c02:s01']]),
      'arr_guidance_bridge':table({'fiscal_year':TEXT,'observed_exit_arr_usd_billion':numeric('usd_billion'),'revalued_opening_arr_usd_billion':numeric('usd_billion'),
           'revaluation_usd_million':MONEY,'target_arr_growth_pct':PERCENT,'implied_target_arr_usd_billion':numeric('usd_billion')},['fiscal_year'],[['c02:s02']])}
    return {
      'a02':{'source':'meta-fy2025','calculate':meta_reference,'tables':cash_tables,
        'sql':{'cash_model':META_CASH_SQL,'operating_cash_bridge':META_BRIDGE_SQL,'segment_model':META_SEGMENT_SQL},
        'claims':{'annual_fcf_increased':claim('contradicted',['a02:s01','a02:s03'],'FY2025 free cash flow exceeded FY2024 free cash flow on the issuer definition.'),
                  'foa_income_covers_rl_loss':claim('supported',['a02:s02'],'FY2025 Family of Apps operating income exceeds the absolute Reality Labs operating loss.'),
                  'tax_adjustment_future_cash_identifiable':claim('unresolved',['a02:s01'],'The supplied cash-flow statement identifies the exact future cash-tax saving caused by its deferred-tax adjustment.')},
        'request':'Update the cash-generation and segment workpaper through Meta FY2025. Preserve FY2024, reconstruct the first nine months from full-year and Q4 disclosures, and report Q4, first-nine-month and annual outputs for both years. Reconcile operating cash flow from net income, noncash adjustments and operating working-capital changes. Apply the issuer free-cash-flow definition, including finance-lease principal. Reconstruct both segment margins without double-counting advertising within Family of Apps.',
        'definitions':{'cash_model':'months=3 denotes Q4, months=9 the first nine months and months=12 the fiscal year. Spending and lease principal are positive outflow amounts. FCF less net income is a difference of period flows.',
                      'operating_cash_bridge':'Residual is net income plus the disclosed noncash adjustments and operating-asset/liability changes less reported operating cash flow. Other means the row in operating cash adjustments, not other investing or financing activities.',
                      'segment_model':'Family of Apps and Reality Labs are separate segment keys, with operating margin in percent.'},
        'rationale':'An analyst updating a cash-conversion model must reconcile statement sections and retain lease-funded capital spending. The period bridge and segment model provide different views of economic performance, while a noncash tax adjustment alone cannot quantify a future cash benefit.'},
      'b02':{'source':'paxos-pyusd-2026','calculate':paxos_reference,'tables':paxos_tables,
        'sql':{'qualified_coverage':PAXOS_COVERAGE_SQL,'treasury_valuation':PAXOS_TREASURY_SQL,'stock_bridge':PAXOS_BRIDGE_SQL},
        'claims':{'jan16_year_uniquely_resolved':claim('contradicted',['b02:s03'],'The supplied January report uses one consistent year for its January 16 observation.'),
                  'all_clear_dates_fully_backed':claim('supported',['b02:s01','b02:s02','b02:s05'],'At each requested unambiguous observation date, redemption assets exceed redeemable tokens at USD 1 per token.'),
                  'payments_volume_identifiable':claim('unresolved',['b02:s04'],'The supplied reserve and token snapshots identify payments volume between January 30 and February 27.')},
        'request':'Audit the PYUSD valuation workpaper against the January and February 2026 reports. Repair identifiable valuation errors, retain valid stock-bridge behavior, and report coverage at January 30, February 10 and February 27 at their disclosed observation times. Reconcile Treasury holdings at fair value to the reported asset category, retain separate par and cost comparisons, and build adjacent stock-change bridges. Address the January 16 date conflict without assigning an invented year. Do not count repo collateral as additional Treasury assets.',
        'definitions':{'qualified_coverage':'Assets are cash plus repo fair value plus deduplicated Treasury-holding fair value. Residual is recomputed assets less reported assets. Signature lag is calendar days from economic observation to signature, not a public posting delay.',
                      'treasury_valuation':'Holdings are keyed by economic_date and cusip. Identical export repetitions are one holding, distinct CUSIPs with equal values remain separate. Valuation gain is fair value less cost, discount_to_par is fair value less par.',
                      'stock_bridge':'Use January 30 to February 10 and February 10 to February 27. Changes are current less prior stocks, with surplus change equal to asset change less redeemable-token change.'},
        'rationale':'Reserve adequacy depends on valuation basis, holding identity and economic-date scope. A real internal date conflict remains unresolved alongside useful calculations on unambiguous dates. Authored par-versus-fair-value errors are distinct from the issuer discrepancy.'},
      'c02':{'source':'adobe-fy2025','calculate':adobe_reference,'tables':adobe_tables,
        'sql':{'operating_reconciliation':ADOBE_RECON_SQL,'adjustment_attribution':ADOBE_ATTRIBUTION_SQL,'arr_guidance_bridge':ADOBE_ARR_SQL},
        'claims':{'adjusted_growth_slower_than_gaap':claim('supported',['c02:s01'],'Annual non-GAAP operating income grew more slowly than GAAP operating income from FY2024 to FY2025.'),
                  'arr_revaluation_is_recognized_revenue':claim('contradicted',['c02:s02','c02:s03'],'The USD 460 million ARR revaluation is recognized FY2025 revenue.'),
                  'exact_organic_arr_increase_identifiable':claim('unresolved',['c02:s02'],'The supplied disclosure separately quantifies the exact organic customer contribution to the ARR revaluation.')},
        'request':'Reconcile Adobe FY2025 GAAP and adjusted operating performance before using next-year ARR guidance. Preserve each disclosed quarterly comparison, quantify the annual change in the adjustment gap by component, and show why growth rates differ. Build an ARR basis bridge from observed FY2025 exit to revalued FY2026 opening and the mechanically implied target on the disclosed growth basis. Keep forecasts and ARR stock measures distinct from recognized revenue.',
        'definitions':{'operating_reconciliation':'Include FY2024, FY2025, Q4FY2024, Q3FY2025 and Q4FY2025. Residual is GAAP plus adjustment rows less reported non-GAAP operating income.',
                      'adjustment_attribution':'Each contribution divides its FY2025 less FY2024 change by the change in the total non-GAAP minus GAAP adjustment gap. Signed contributions may exceed 100% or be negative.',
                      'arr_guidance_bridge':'Use the revalued opening FY2026 ARR basis for the 10.2% target. The implied target is arithmetic on rounded disclosure amounts, not an observed forecast outcome.'},
        'rationale':'An analyst can misattribute better GAAP growth to recurring performance when a prior acquisition expense leaves the adjusted measure. ARR guidance requires another basis reconciliation, and a currency-driven revaluation does not identify organic sales or recognized revenue.'}}


def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for row in rows:
            for field,value in row.items():
                if isinstance(value,(int,float)) and field not in ('fiscal_year','months') and not field.endswith('_pct'):
                    if key=='c02' and field=='value' and row.get('measure','').endswith('_pct'):
                        continue
                    row[field]=value*2
    yield 'scaled_amounts_preserve_ratios',scaled
    changed=copy.deepcopy(data)
    if key=='a02':
        offsets={'Purchases of property and equipment':-500,'Principal payments on finance leases':500,
                 'Net cash used in investing activities':-500,'Net cash used in financing activities':500}
        for row in changed['cashflows']:
            if row['fiscal_year']==2025 and row['measure'] in offsets:row['amount']+=offsets[row['measure']]
        yield 'capital_spending_mix_changes_fcf_preserved',changed
    elif key=='b02':
        first=next(r for r in changed['treasury_holdings'] if r['economic_date']=='2026-01-30')
        first['fair_value_usd']+=10000
        for row in changed['reserve_observations']:
            if row['economic_date']=='2026-01-30':
                row['treasury_fair_value_usd']+=10000
                row['reported_assets_usd']+=10000
        yield 'valuation_change_reconciles',changed
        duplicate=copy.deepcopy(data)
        duplicate['treasury_holdings'].append(copy.deepcopy(duplicate['treasury_holdings'][0]))
        yield 'identical_export_is_one_holding',duplicate
        equal=copy.deepcopy(data)
        first,second=equal['treasury_holdings'][:2]
        delta=first['fair_value_usd']-second['fair_value_usd']
        for field in ('par_usd','cost_usd','fair_value_usd'):second[field]=first[field]
        for row in equal['reserve_observations']:
            if row['economic_date']=='2026-01-30':
                row['treasury_fair_value_usd']+=delta
                row['reported_assets_usd']+=delta
        yield 'distinct_equal_value_holdings_remain',equal
        return
    else:
        for row in changed['operating_reconciliation']:
            if row['period']=='FY2024' and row['measure']=='acquisition_expense':row['amount']+=100
            if row['period']=='FY2024' and row['measure']=='gaap_operating_income':row['amount']-=100
        yield 'prior_acquisition_adjustment_changes_attribution',changed
    later=copy.deepcopy(data)
    names=('cashflows','segments') if key=='a02' else ('operating_reconciliation',)
    for name in names:
        added=copy.deepcopy(later[name])
        for row in added:
            if key=='a02':row['fiscal_year']=2026
            else:row['period']=row['period'].replace('2025','2026').replace('2024','2027')
        later[name]+=added
    yield 'irrelevant_later_disclosure',later
