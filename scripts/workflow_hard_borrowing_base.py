"""Collateral concentration limits and the cash cost of inventory funding."""
import copy
import json
from decimal import Decimal
from pathlib import Path

D = lambda value: Decimal(str(value))


def components(data, case, seasonal):
    f = data['facility_terms'][0]
    rate = D(f['seasonal_inventory_rate'] if seasonal else f['ordinary_inventory_rate'])
    u = D(f['receivable_rate'])*(D(case['credit_card_receivables'])+D(case['pharmacy_receivables'])) + rate*D(case['regular_inventory_cost'])*D(case['regular_appraisal'])
    p = rate*D(case['perishable_inventory_cost'])*D(case['perishable_appraisal'])
    s = D(f['script_rate'])*D(case['script_liquidation_value'])
    r = D(case['availability_reserves'])
    du = rate*D(case['regular_appraisal'])*D(case['regular_purchase_fraction'])
    dp = rate*D(case['perishable_appraisal'])*(1-D(case['regular_purchase_fraction']))
    return f, u, p, s, r, du, dp


def certificate(f, u, p, s, r):
    q = D(f['shared_fraction'])/(1-D(f['shared_fraction']))
    k = D(f['perishable_fraction'])/(1-D(f['perishable_fraction']))
    scripts = min(s,D(f['shared_dollar_cap']),q*(u+p-r))
    perishables = min(p,k*(u+s-r))
    return u+scripts+perishables-r


def calculate(data):
    certificates, proposals, limits = [], [], []
    for c in data['collateral_cases']:
        for period in data['period_cases']:
            f,u,p,s,r,du,dp = components(data,c,period['seasonal'])
            exposure = D(c['loans'])+D(c['letters_of_credit'])
            commitment = D(f['commitment'])
            b = certificate(f,u,p,s,r)
            assert min(commitment,b)>=exposure
            certificates.append([c['scenario'],period['period'],float(u+p+s-r),float(b),float(min(commitment,b)-exposure)])
            for proposal in data['purchase_sizes']:
                cost = D(proposal['purchase_cost'])
                after = certificate(f,u+du*cost,p+dp*cost,s,r)
                slack = min(commitment,after)-exposure-cost
                proposals.append([c['scenario'],period['period'],proposal['proposal'],float(after),float(exposure+cost),float(slack),int(slack>=0)])
            # Each concentration-limited contribution is the minimum of affine
            # expressions. Their sum is the minimum over all paired branches.
            q = D(f['shared_fraction'])/(1-D(f['shared_fraction']))
            k = D(f['perishable_fraction'])/(1-D(f['perishable_fraction']))
            bounds = [commitment-exposure]
            for si,ss in [(s,D(0)),(D(f['shared_dollar_cap']),D(0)),(q*(u+p-r),q*(du+dp))]:
                for pi,ps in [(p,dp),(k*(u+s-r),k*du)]:
                    intercept,slope = u+si+pi-r,du+ss+ps
                    if slope<1:bounds.append((intercept-exposure)/(1-slope))
            maximum = min(bounds)
            after = certificate(f,u+du*maximum,p+dp*maximum,s,r)
            limits.append([c['scenario'],period['period'],float(maximum),float(after),float(min(commitment,after)-exposure-maximum)])
    return {'certificates':certificates,'purchase_plans':proposals,'funding_limits':limits}


BASE = """WITH inputs AS (
 SELECT c.*,f.*,period,seasonal,
 CASE WHEN seasonal=1 THEN seasonal_inventory_rate ELSE ordinary_inventory_rate END rate,
 loans+letters_of_credit exposure FROM collateral_cases c CROSS JOIN facility_terms f CROSS JOIN period_cases
), raw AS (
 SELECT *,receivable_rate*(credit_card_receivables+pharmacy_receivables)+rate*regular_inventory_cost*regular_appraisal u,
 rate*perishable_inventory_cost*perishable_appraisal p,script_rate*script_liquidation_value s,
 availability_reserves r,rate*regular_appraisal*regular_purchase_fraction du,
 rate*perishable_appraisal*(1-regular_purchase_fraction) dp,
 shared_fraction/(1-shared_fraction) q,perishable_fraction/(1-perishable_fraction) k FROM inputs
) """
CERT = "u+MIN(s,shared_dollar_cap,q*(u+p-r))+MIN(p,k*(u+s-r))-r"
POST = "u+du*purchase_cost+MIN(s,shared_dollar_cap,q*(u+p+(du+dp)*purchase_cost-r))+MIN(p+dp*purchase_cost,k*(u+du*purchase_cost+s-r))-r"
SQL = {
 'certificates': BASE+", valued AS (SELECT *,"+CERT+" b FROM raw) SELECT scenario,period,u+p+s-r uncapped_advance_usd_million,b borrowing_base_usd_million,MIN(commitment,b)-exposure available_draw_usd_million FROM valued",
 'purchase_plans': BASE+", valued AS (SELECT *,"+POST+" b FROM raw CROSS JOIN purchase_sizes) SELECT scenario,period,proposal,b borrowing_base_usd_million,exposure+purchase_cost revolving_exposure_usd_million,MIN(commitment,b)-exposure-purchase_cost funding_surplus_usd_million,CASE WHEN MIN(commitment,b)>=exposure+purchase_cost THEN 1 ELSE 0 END feasible FROM valued",
 'funding_limits': BASE+""", script_branches AS (
 SELECT scenario,period,s intercept,0.0 slope FROM raw UNION ALL
 SELECT scenario,period,shared_dollar_cap,0.0 FROM raw UNION ALL
 SELECT scenario,period,q*(u+p-r),q*(du+dp) FROM raw
), perishable_branches AS (
 SELECT scenario,period,p intercept,dp slope FROM raw UNION ALL
 SELECT scenario,period,k*(u+s-r),k*du FROM raw
), bounds AS (
 SELECT scenario,period,commitment-exposure bound FROM raw UNION ALL
 SELECT a.scenario,a.period,(u+s.intercept+p.intercept-r-exposure)/(1-du-s.slope-p.slope)
 FROM raw a JOIN script_branches s USING(scenario,period) JOIN perishable_branches p USING(scenario,period)
 WHERE du+s.slope+p.slope<1
), limits AS (SELECT scenario,period,MIN(bound) purchase_cost FROM bounds GROUP BY scenario,period), valued AS (
 SELECT a.*,purchase_cost,"""+POST+""" b FROM raw a JOIN limits USING(scenario,period)
)
SELECT scenario,period,purchase_cost maximum_purchase_usd_million,b borrowing_base_usd_million,
 MIN(commitment,b)-exposure-purchase_cost funding_surplus_usd_million FROM valued"""}


def alternatives():
    # Numerical monotone feasibility search does not enumerate binding caps.
    alt = dict(SQL)
    alt['funding_limits'] = BASE.replace('WITH inputs','WITH RECURSIVE inputs')+""", search(scenario,period,step,lo,hi) AS (
 SELECT scenario,period,0,0.0,commitment-exposure FROM raw UNION ALL
 SELECT z.scenario,z.period,step+1,
 CASE WHEN MIN(commitment,"""+POST.replace('purchase_cost','((lo+hi)/2)')+""")>=exposure+(lo+hi)/2 THEN (lo+hi)/2 ELSE lo END,
 CASE WHEN MIN(commitment,"""+POST.replace('purchase_cost','((lo+hi)/2)')+""")>=exposure+(lo+hi)/2 THEN hi ELSE (lo+hi)/2 END
 FROM search z JOIN raw USING(scenario,period) WHERE step<60
), valued AS (SELECT raw.*,lo purchase_cost,"""+POST.replace('purchase_cost','lo')+""" b FROM search JOIN raw USING(scenario,period) WHERE step=60)
SELECT scenario,period,purchase_cost maximum_purchase_usd_million,b borrowing_base_usd_million,
 MIN(commitment,b)-exposure-purchase_cost funding_surplus_usd_million FROM valued"""
    # Solve the two single-cap fixed points instead of rearranging percentages.
    alt['certificates'] = BASE+""", counterfactuals AS (
 SELECT *,MIN(u+p+s-r,u+p+shared_dollar_cap-r,(u+p-r)/(1-shared_fraction)) without_perishables,
 MIN(u+s+p-r,(u+s-r)/(1-perishable_fraction)) without_shared FROM raw
), valued AS (
 SELECT *,u+MIN(s,shared_dollar_cap,shared_fraction*without_perishables)+MIN(p,perishable_fraction*without_shared)-r b FROM counterfactuals
)
SELECT scenario,period,u+p+s-r uncapped_advance_usd_million,b borrowing_base_usd_million,
 MIN(commitment,b)-exposure available_draw_usd_million FROM valued"""
    return alt


def table(columns, keys):
    return {'columns':{c:({'type':'text','unit':'label'} if c in keys else {'type':'integer','unit':'indicator'} if c=='feasible' else {'type':'real','unit':'usd_million','tolerance':1e-7}) for c in columns},'keys':keys,'row_order':'ignored','duplicates':'Keys must be unique','evidence':[['a01:s01','a01:s02','a01:s03','a01:s05'],['a01:s02','a01:s03','a01:s04','a01:s05']],'context_evidence_allowed':[]}


def specification():
    source=json.loads((Path(__file__).resolve().parents[1]/'datasets/workflow-hard-eval-v1/sources/albertsons-2025.json').read_text())
    support=[['a01:s01','a01:s02','a01:s03','a01:s05'],['a01:s02','a01:s03','a01:s04','a01:s05']]
    def claim(assertion,verdict):return {'assertion':assertion,'verdict':verdict,'evidence':support,'context_evidence_allowed':[]}
    return {'source':'albertsons-2025','calculate':calculate,'sql':SQL,
      'title':'Albertsons collateral availability and inventory purchase funding',
      'nearest':['workflow-hard-pilot-v2/a01','workflow-hard-pilot-v1/c01'],
      'novelty':'Reconstruct collateral capacity from concentration definitions with distinct counterfactual denominators, then connect an inventory purchase to both its cash funding and its changing collateral value. Reverse-solve the largest self-funded purchase across binding regimes.',
      'request':'For the hypothetical eligible-collateral cases, apply the August 27, 2025 Albertsons ABL terms to prepare borrowing-base certificates for ordinary and seasonal advance rates. Test each stated inventory purchase and calculate the largest purchase that the facility can fund under each case. Use the prescribed purchase mix and post-purchase collateral values. These are conditional credit-capacity calculations, not observed issuer availability or legal transaction approvals.',
      'assumptions':source['assumptions'],
      'definitions':{
        'certificates':'One row per collateral scenario and period. uncapped_advance is the advance value after reserves with concentration limits removed. borrowing_base applies the disclosed concentration limits. available_draw is the additional cash borrowing available before any purchase, after existing loans and letters of credit.',
        'purchase_plans':'One row per scenario, period and purchase proposal. Report the post-purchase borrowing_base, total revolving_exposure including required purchase borrowing and letters of credit, and funding_surplus equal to the applicable loan limit less that total exposure. A negative surplus is a funding shortfall. feasible is 1 if the purchase can be funded and 0 otherwise.',
        'funding_limits':'One row per scenario and period. Report the sharp maximum continuous purchase cost, the resulting borrowing_base and funding_surplus on the same basis as purchase_plans. Do not report a selected arbitrary near-limit purchase or an allocation witness.'},
      'tables':{
        'certificates':table(['scenario','period','uncapped_advance_usd_million','borrowing_base_usd_million','available_draw_usd_million'],['scenario','period']),
        'purchase_plans':table(['scenario','period','proposal','borrowing_base_usd_million','revolving_exposure_usd_million','funding_surplus_usd_million','feasible'],['scenario','period','proposal']),
        'funding_limits':table(['scenario','period','maximum_purchase_usd_million','borrowing_base_usd_million','funding_surplus_usd_million'],['scenario','period'])},
      'claims':{
        'capacity_only':claim('In case_b at ordinary advance rates, unused aggregate commitment is sufficient evidence that plan_2 can be fully funded.','contradicted'),
        'collateral_feedback':claim('In case_a at ordinary advance rates, the largest permitted purchase exceeds the cash borrowing available before that purchase.','supported'),
        'issuer_actual':claim('Albertsons actual excess availability was at least USD 1,000 million on August 27, 2025.','unresolved')}}


def controls(data):
    result=[]
    def changed(name,why,fn):
        x=copy.deepcopy(data);fn(x);result.append((name,why,x))
    changed('row_order','Ordering of input rows has no financial meaning.',lambda x:[v.reverse() for v in x.values()])
    def scale(x):
        monetary={'commitment','lc_sublimit','swingline_sublimit','shared_dollar_cap','credit_card_receivables','pharmacy_receivables','script_liquidation_value','regular_inventory_cost','perishable_inventory_cost','availability_reserves','loans','letters_of_credit','purchase_cost'}
        for rows in x.values():
            for row in rows:
                for key in row:
                    if key in monetary:row[key]*=2
    changed('scale','Scale every monetary input, including dollar caps, while retaining rates.',scale)
    changed('letters_of_credit','Letters of credit consume aggregate facility capacity.',lambda x:x['collateral_cases'][1].update(letters_of_credit=225))
    changed('reserves','Additional reserves affect concentration denominators as well as total collateral.',lambda x:x['collateral_cases'][0].update(availability_reserves=350))
    changed('purchase_mix','Changing inventory composition changes collateral created by the same cash purchase.',lambda x:x['collateral_cases'][1].update(regular_purchase_fraction=.9))
    changed('commitment','Lower lender commitment can bind independently of collateral capacity.',lambda x:x['facility_terms'][0].update(commitment=3500))
    changed('dollar_cap','A higher scripts dollar cap exposes the distinct percentage limit.',lambda x:x['facility_terms'][0].update(shared_dollar_cap=1400))
    changed('sublimits','Unused subfacility size alone does not create aggregate borrowing capacity.',lambda x:x['facility_terms'][0].update(lc_sublimit=1700,swingline_sublimit=300))
    changed('seasonal_rate','The applicable inventory rate affects both collateral categories and the funding frontier.',lambda x:x['facility_terms'][0].update(seasonal_inventory_rate=.95))
    return result


def mistakes():
    return {
      'ignore_concentration_caps':{'table':'certificates','sql':SQL['certificates'].replace(CERT,'u+p+s-r')},
      'percent_of_uncapped_total':{'table':'certificates','sql':SQL['certificates'].replace('q*(u+p-r)','shared_fraction*(u+p+s-r)').replace('k*(u+s-r)','perishable_fraction*(u+p+s-r)')},
      'exclude_reserves_from_denominators':{'table':'certificates','sql':SQL['certificates'].replace('q*(u+p-r)','q*(u+p)').replace('k*(u+s-r)','k*(u+s)')},
      'add_subfacility_to_commitment':{'table':'purchase_plans','sql':SQL['purchase_plans'].replace('MIN(commitment,b)','MIN(commitment+lc_sublimit+swingline_sublimit,b)')},
      'omit_letters_of_credit':{'table':'purchase_plans','sql':SQL['purchase_plans'].replace('loans+letters_of_credit exposure','loans exposure')},
      'ignore_new_collateral':{'table':'funding_limits','sql':BASE+", v AS (SELECT *,"+CERT+" b FROM raw) SELECT scenario,period,MIN(commitment,b)-exposure maximum_purchase_usd_million,b borrowing_base_usd_million,0.0 funding_surplus_usd_million FROM v"},
      'purchase_value_not_cost':{'table':'purchase_plans','sql':SQL['purchase_plans'].replace('exposure+purchase_cost','exposure+(du+dp)*purchase_cost').replace('-exposure-purchase_cost','-exposure-(du+dp)*purchase_cost')},
      'ordinary_rate_all_periods':{'table':'certificates','sql':SQL['certificates'].replace('CASE WHEN seasonal=1 THEN seasonal_inventory_rate ELSE ordinary_inventory_rate END','ordinary_inventory_rate')}
    }
