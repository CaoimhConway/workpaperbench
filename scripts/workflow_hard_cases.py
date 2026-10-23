"""Financial references and counterfactuals for the experimental development tier."""
import copy
from decimal import Decimal
from itertools import product

D = lambda x: Decimal(str(x))
MONEY = {'type': 'real', 'unit': 'million', 'tolerance': 0.000001}
PERCENT = {'type': 'real', 'unit': 'percent', 'tolerance': 0.000001}
TEXT = {'type': 'text', 'unit': 'label'}


def spec(columns, keys, evidence, unit='usd_million', context=()):
    result = {'columns': {}, 'keys': keys, 'row_order': 'ignored', 'duplicates': 'Keys must be unique',
              'evidence': evidence, 'context_evidence_allowed': list(context)}
    for name, kind in columns:
        result['columns'][name] = copy.deepcopy({'text': TEXT, 'money': MONEY, 'pct': PERCENT}[kind])
        if kind == 'money':
            result['columns'][name]['unit'] = unit
    return result


def rows(data, name):
    return data[name]


def ahold(data):
    current = {r['segment']: D(r['ifrs']) + D(r['divestments']) + D(r['calendar']) for r in data['quarter_current']}
    matched = {r['segment']: D(r['q42015_matched']) for r in data['matched_quarter']}
    quarter, periods = [], []
    extra = D(0)
    for row in data['period_sales']:
        key = row['segment']
        week = D(row['q42015']) - matched[key]
        extra += week
        quarter.append([key, float(current[key]), float(week), float(current[key] - matched[key]),
                        float(100 * (current[key] / matched[key] - 1))])
        for label, now, before in (
            ('fy', D(row['fy2016']), D(row['fy2015']) - week),
            ('q4', current[key], matched[key]),
            ('pre_q4', D(row['fy2016']) - current[key], D(row['fy2015']) - D(row['q42015']))):
            periods.append([key, label, float(now), float(before), float(now-before), float(100*(now/before-1))])
    g = {r['year']: r for r in data['group_annual']}
    statutory = D(g[2016]['ifrs'])-D(g[2015]['ifrs'])
    presentation = (D(g[2016]['proforma'])-D(g[2016]['ifrs']))-(D(g[2015]['proforma'])-D(g[2015]['ifrs']))
    comparable = statutory+presentation+extra
    segment_change = sum((D(r['fy2016'])-D(r['fy2015']) for r in data['period_sales']),D(0))+extra
    return {'quarter_scope': quarter, 'comparable_periods': periods,
            'annual_change_bridge': [[float(statutory),float(presentation),float(extra),float(comparable),
                float(100*comparable/(D(g[2015]['proforma'])-extra)),float(segment_change-comparable)]]}


def microsoft(data):
    c, a = data['cash_flows'][0], data['annual_expenses'][0]
    p = {r['year']: r for r in data['ppe']}
    f = {r['year']: r for r in data['finance_leases']}
    purchase = D(c['cash_ppe'])
    payables = 1000*(D(p[2025]['capital_payables_billion'])-D(p[2024]['capital_payables_billion']))
    proxy = purchase+payables
    additions, depreciation = D(a['finance_rou_additions']), 1000*D(a['ppe_depreciation_billion'])
    net_change = D(p[2025]['net'])-D(p[2024]['net'])
    explained = proxy+additions-depreciation
    lease = []
    for label, expected in [('gross',additions),('accumulated',D(a['finance_amortization'])),
                             ('net',additions-D(a['finance_amortization']))]:
        delta = D(f[2025][label])-D(f[2024][label])
        lease.append([label,float(delta),float(expected),float(delta-expected)])
    return {'cash_investment': [[float(purchase),a['finance_principal_cash'],
             float(purchase+D(a['finance_principal_cash'])),float(additions)]],
            'ppe_bridge': [[float(payables),float(proxy),float(additions),float(depreciation),
                            float(net_change),float(explained),float(net_change-explained)]],
            'lease_movements': lease}


def vertices(capacities, services):
    """Extreme points of a three-country bounded allocation with one sum constraint."""
    found = set()
    for free in range(3):
        fixed = [i for i in range(3) if i != free]
        for limits in product((0, 1), repeat=2):
            allocation = [D(0)]*3
            for i, bound in zip(fixed, limits):
                allocation[i] = capacities[i] if bound else D(0)
            allocation[free] = services-sum(allocation)
            if 0 <= allocation[free] <= capacities[free]:
                found.add(tuple(allocation))
    if not found:
        raise ValueError('infeasible_marginals')
    return sorted(found)


def apple(data):
    lines = {r['business_line']: r for r in data['business_lines']}
    regions = sorted(data['geographies'], key=lambda r:r['geography'])
    rates = {r['geography']: r for r in data['stress_rates']}
    margins = {k:(D(r['net_sales'])-D(r['cost_of_sales']))/D(r['net_sales']) for k,r in lines.items()}
    total = sum((D(r['net_sales']) for r in lines.values()),D(0))
    services = D(lines['services']['net_sales'])
    capacities = [D(r['net_sales']) for r in regions]
    assert sum(capacities) == total
    mix = [[k,r['net_sales'],float(D(r['net_sales'])-D(r['cost_of_sales'])),float(100*margins[k])] for k,r in lines.items()]
    regional = [[r['geography'],float(max(D(0),D(r['net_sales'])-services)),
                 float(min(D(r['net_sales']),D(lines['products']['net_sales'])))] for r in regions]
    bounds = []
    for measure in ('revenue','gross_profit'):
        weight = {'products':D(1),'services':D(1)} if measure=='revenue' else margins
        losses = []
        for allocation in vertices(capacities,services):
            loss = sum(((cap-s)*D(rates[r['geography']]['products_loss_pct'])/100*weight['products']+
                        s*D(rates[r['geography']]['services_loss_pct'])/100*weight['services']
                        for cap,s,r in zip(capacities,allocation,regions)),D(0))
            losses.append(loss)
        base = total if measure=='revenue' else sum((D(r['net_sales'])-D(r['cost_of_sales']) for r in lines.values()),D(0))
        bounds.append([measure,float(min(losses)),float(max(losses)),float(100*min(losses)/base),float(100*max(losses)/base)])
    return {'worldwide_mix':mix,'regional_product_bounds':regional,'stress_bounds':bounds}


AHOLD_CTE = """WITH q AS (
 SELECT c.segment,c.ifrs+c.divestments+c.calendar current_q4,
 p.fy2016,p.fy2015,p.q42015,m.q42015_matched,
 p.q42015-m.q42015_matched extra_week
 FROM quarter_current c JOIN period_sales p USING(segment) JOIN matched_quarter m USING(segment)
) """
AHOLD_SQL = {
 'quarter_scope': AHOLD_CTE+"""SELECT segment,current_q4 proforma_q42016_eur_million,
 extra_week extra_week2015_eur_million,current_q4-q42015_matched change_eur_million,
 100.0*(current_q4/q42015_matched-1) growth_pct FROM q""",
 'comparable_periods': AHOLD_CTE+""", periods AS (
 SELECT segment,'fy' period,fy2016 current,fy2015-extra_week prior FROM q
 UNION ALL SELECT segment,'q4',current_q4,q42015_matched FROM q
 UNION ALL SELECT segment,'pre_q4',fy2016-current_q4,fy2015-extra_week-q42015_matched FROM q
) SELECT segment,period,current current_eur_million,prior prior_eur_million,
 current-prior change_eur_million,100.0*(current/prior-1) growth_pct FROM periods""",
 'annual_change_bridge': AHOLD_CTE+""", g AS (
 SELECT MAX(CASE WHEN year=2016 THEN ifrs END) i1,MAX(CASE WHEN year=2015 THEN ifrs END) i0,
 MAX(CASE WHEN year=2016 THEN proforma END) p1,MAX(CASE WHEN year=2015 THEN proforma END) p0 FROM group_annual
), s AS (SELECT SUM(extra_week) w,SUM(fy2016-fy2015+extra_week) delta FROM q)
 SELECT i1-i0 statutory_change_eur_million,(p1-i1)-(p0-i0) presentation_change_eur_million,
 w prior_extra_week_eur_million,p1-p0+w comparable_change_eur_million,
 100.0*(p1-p0+w)/(p0-w) comparable_growth_pct,delta-(p1-p0+w) segment_residual_eur_million FROM g CROSS JOIN s"""}
MS_CTE = """WITH b AS (SELECT c.cash_ppe,a.*,1000.0*(p.capital_payables_billion-o.capital_payables_billion) payable_change,
 p.net-o.net net_change FROM cash_flows c JOIN annual_expenses a USING(year)
 JOIN ppe p ON p.year=c.year JOIN ppe o ON o.year=c.year-1) """
MICROSOFT_SQL = {
 'cash_investment': MS_CTE+"""SELECT cash_ppe cash_ppe_usd_million,finance_principal_cash principal_usd_million,
 cash_ppe+finance_principal_cash capital_cash_usd_million,finance_rou_additions noncash_lease_additions_usd_million FROM b""",
 'ppe_bridge': MS_CTE+"""SELECT payable_change payables_change_usd_million,cash_ppe+payable_change purchase_proxy_usd_million,
 finance_rou_additions lease_additions_usd_million,1000.0*ppe_depreciation_billion depreciation_usd_million,
 net_change net_change_usd_million,cash_ppe+payable_change+finance_rou_additions-1000.0*ppe_depreciation_billion explained_change_usd_million,
 net_change-(cash_ppe+payable_change+finance_rou_additions-1000.0*ppe_depreciation_billion) residual_usd_million FROM b""",
 'lease_movements': """WITH l AS (SELECT c.gross-p.gross gross,c.accumulated-p.accumulated accumulated,c.net-p.net net,
 a.finance_rou_additions additions,a.finance_amortization amort FROM finance_leases c JOIN finance_leases p ON p.year=c.year-1
 JOIN annual_expenses a ON a.year=c.year), bridge AS (
 SELECT 'gross' measure,gross observed,additions explained FROM l UNION ALL
 SELECT 'accumulated',accumulated,amort FROM l UNION ALL SELECT 'net',net,additions-amort FROM l)
 SELECT measure,observed change_usd_million,explained explained_change_usd_million,observed-explained residual_usd_million FROM bridge"""}
APPLE_CTE = """WITH lines AS (SELECT MAX(CASE WHEN business_line='products' THEN net_sales END) p,
 MAX(CASE WHEN business_line='services' THEN net_sales END) s,
 MAX(CASE WHEN business_line='products' THEN (net_sales-cost_of_sales)/net_sales END) pm,
 MAX(CASE WHEN business_line='services' THEN (net_sales-cost_of_sales)/net_sales END) sm FROM business_lines),
 r AS (SELECT g.*,s.products_loss_pct/100.0 pr,s.services_loss_pct/100.0 sr,
 ROW_NUMBER() OVER(ORDER BY g.geography) rn FROM geographies g JOIN stress_rates s USING(geography)) """
APPLE_SQL = {
 'worldwide_mix': """SELECT business_line,net_sales net_sales_usd_million,net_sales-cost_of_sales gross_profit_usd_million,
 100.0*(net_sales-cost_of_sales)/net_sales gross_margin_pct FROM business_lines""",
 'regional_product_bounds': APPLE_CTE+"""SELECT geography,MAX(0,net_sales-s) lower_usd_million,
 MIN(net_sales,p) upper_usd_million FROM r CROSS JOIN lines""",
 'stress_bounds': APPLE_CTE+""", limits AS (SELECT 0 bound UNION ALL SELECT 1),
 candidates AS (SELECT a.geography ga,b.geography gb,c.geography gc,
 a.net_sales*x.bound sa,b.net_sales*y.bound sb,s-a.net_sales*x.bound-b.net_sales*y.bound sc
 FROM r a JOIN r b ON a.rn<b.rn JOIN r c ON c.rn!=a.rn AND c.rn!=b.rn
 CROSS JOIN limits x CROSS JOIN limits y CROSS JOIN lines
 WHERE s-a.net_sales*x.bound-b.net_sales*y.bound BETWEEN 0 AND c.net_sales),
 objectives AS (SELECT 'revenue' measure,1.0 pw,1.0 sw,p+s base FROM lines UNION ALL
 SELECT 'gross_profit',pm,sm,p*pm+s*sm FROM lines),
 losses AS (SELECT o.measure,o.base,v.ga,v.gb,v.gc,v.sa,v.sb,v.sc,
 SUM((r.net_sales-CASE r.geography WHEN v.ga THEN v.sa WHEN v.gb THEN v.sb ELSE v.sc END)*r.pr*o.pw+
 (CASE r.geography WHEN v.ga THEN v.sa WHEN v.gb THEN v.sb ELSE v.sc END)*r.sr*o.sw) loss
 FROM candidates v CROSS JOIN r CROSS JOIN objectives o GROUP BY o.measure,o.base,v.ga,v.gb,v.gc,v.sa,v.sb,v.sc)
 SELECT measure,MIN(loss) lower_usd_million,MAX(loss) upper_usd_million,
 100.0*MIN(loss)/base lower_pct,100.0*MAX(loss)/base upper_pct FROM losses GROUP BY measure,base"""}


def specifications():
    return {
      'a01': {'source':'ahold-2016','calculate':ahold,'sql':AHOLD_SQL,
        'title':'Ahold Delhaize comparable sales across merger scope and calendars',
        'nearest':['workflow-v15/c07','workflow-v15/a03'],
        'novelty':'Reconstruct comparable numerical sales and an additive annual presentation bridge, including a nonuniform extra week and its cancellation in pre-Q4 periods. This goes beyond judging unequal acquisition duration or subtracting cumulative quarters on a single basis.',
        'request':'Prepare a 2016-versus-2015 sales workpaper for Ahold Delhaize. Use the disclosed pro forma business perimeter at reported exchange rates. Match durations between years within each former business by excluding the additional former-Ahold week in 2015. Retain the different former-Ahold and former-Delhaize reporting calendars. Reconstruct Q4 2016 from the IFRS and adjustment disclosures, report segment comparisons for FY, Q4 and the pre-Q4 reporting period, and explain the group annual sales-change difference from statutory reporting numerically. This is not an organic, same-store or constant-currency estimate.',
        'definitions':{
          'quarter_scope':'Five segment rows. proforma_q42016 is on the disclosed pro forma perimeter and calendar. extra_week2015 is the prior extra-week sales amount. change and growth compare reconstructed Q4 2016 with the matched-duration Q4 2015. Segment keys are ahold_usa, delhaize_america, netherlands, belgium and cse.',
          'comparable_periods':'Fifteen rows, the five segments for each period fy, q4 and pre_q4. FY and Q4 use the matched-duration comparison. pre_q4 means the respective annual reporting period before the source Q4, not nine calendar months. Growth uses prior sales as denominator. No uniform weekly sales assumption is authorized.',
          'annual_change_bridge':'One row. statutory_change is annual IFRS 2016 less 2015. presentation_change is the current-minus-prior change in pro forma less IFRS sales. prior_extra_week is the positive prior-year extra-week amount. comparable_change is the group matched-duration annual change using independently reported group totals. comparable_growth uses the matched-duration group prior-year denominator. segment_residual is summed segment matched-duration annual changes less the group comparable change. Keep separately reported totals independent.'},
        'tables':{
          'quarter_scope':spec([(x,'text' if x=='segment' else 'pct' if x=='growth_pct' else 'money') for x in ['segment','proforma_q42016_eur_million','extra_week2015_eur_million','change_eur_million','growth_pct']],['segment'],[['a01:s02','a01:s03','a01:s04']],'eur_million'),
          'comparable_periods':spec([(x,'text' if x in ['segment','period'] else 'pct' if x=='growth_pct' else 'money') for x in ['segment','period','current_eur_million','prior_eur_million','change_eur_million','growth_pct']],['segment','period'],[['a01:s02','a01:s03','a01:s04']],'eur_million'),
          'annual_change_bridge':spec([(x,'pct' if x=='comparable_growth_pct' else 'money') for x in ['statutory_change_eur_million','presentation_change_eur_million','prior_extra_week_eur_million','comparable_change_eur_million','comparable_growth_pct','segment_residual_eur_million']],[],[['a01:s03','a01:s04','a01:s05']],'eur_million')},
        'claims':{
          'claim_1':{'assertion':'Every supplied segment has positive pre-Q4 sales growth on the requested basis.','verdict':'supported','evidence':[['a01:s02','a01:s03']]},
          'claim_2':{'assertion':'The requested matched-duration annual sales increase equals the annual statutory IFRS sales increase.','verdict':'contradicted','evidence':[['a01:s03','a01:s04','a01:s05']]},
          'claim_3':{'assertion':'Volume growth alone caused the entire matched-duration pro forma annual sales increase.','verdict':'unresolved','evidence':[['a01:s01','a01:s03','a01:s04']]} }},
      'b01': {'source':'microsoft-2025','calculate':microsoft,'sql':MICROSOFT_SQL,
        'title':'Microsoft cash capital outlay and nested PPE movements',
        'nearest':['workflow-v15/a07','workflow-v15/b10'],
        'novelty':'Distinguish principal cash payments, noncash lease recognition, capital payables and depreciation across cash flow and nested gross/net asset disclosures. Preserve unallocated movement residuals rather than treating cash as asset additions.',
        'request':'Prepare Microsoft consolidated FY2025 capital-investment and asset-movement workpapers for the year ended June 30, 2025. Separate cash outlay from asset recognition and reconcile changes in total PPE and its finance-lease subset from June 30, 2024 to June 30, 2025. Use disclosed point values and retain signed residuals when the supplied disclosures do not completely explain movements. Do not assign those residuals to undocumented acquisitions, disposals or currency movements.',
        'definitions':{
          'cash_investment':'One row. capital_cash is the authored metric cash paid for PPE plus finance-lease principal, excluding interest. noncash_lease_additions are ROU assets obtained for lease obligations, separately reported and outside capital_cash.',
          'ppe_bridge':'One row, all USD million. purchase_proxy is cash PPE payments adjusted for the change in disclosed PPE purchase payables. It is a displayed-value analytical proxy, not a claim of fully identified accounting additions. lease_additions are noncash finance-lease additions. Use the Note 6 PPE depreciation scope, including finance-lease asset amortization, as the bridge convention. explained_change is the net PPE movement attributable to the supplied recognition and consumption disclosures on the specified scope. residual is observed net PPE increase less explained_change. Rounded billion-dollar disclosures remain approximate economic observations even though point arithmetic is graded precisely.',
          'lease_movements':'Three rows keyed gross, accumulated and net. Accumulated depreciation is a positive contra-asset magnitude. change is ending less beginning balance. explained_change is the corresponding movement accounted for by disclosed new finance-lease ROU recognition and finance-lease asset amortization. residual is observed less explained.'},
        'tables':{
          'cash_investment':spec([(x,'money') for x in ['cash_ppe_usd_million','principal_usd_million','capital_cash_usd_million','noncash_lease_additions_usd_million']],[],[['b01:s01','b01:s03']]),
          'ppe_bridge':spec([(x,'money') for x in ['payables_change_usd_million','purchase_proxy_usd_million','lease_additions_usd_million','depreciation_usd_million','net_change_usd_million','explained_change_usd_million','residual_usd_million']],[],[['b01:s01','b01:s02','b01:s03']]),
          'lease_movements':spec([(x,'text' if x=='measure' else 'money') for x in ['measure','change_usd_million','explained_change_usd_million','residual_usd_million']],['measure'],[['b01:s03']])},
        'claims':{
          'claim_1':{'assertion':'FY2025 finance-lease principal cash payments equal the disclosed FY2025 noncash finance-lease ROU additions.','verdict':'contradicted','evidence':[['b01:s03']]},
          'claim_2':{'assertion':'The increase in net finance-lease PPE exceeds FY2025 finance-lease principal cash payments.','verdict':'supported','evidence':[['b01:s03']]},
          'claim_3':{'assertion':'Acquired PPE accounts for the entire total-PPE net bridge residual.','verdict':'unresolved','evidence':[['b01:s01','b01:s02','b01:s03']]}}},
      'c01': {'source':'apple-2024','calculate':apple,'sql':APPLE_SQL,
        'title':'Apple joint revenue exposure and sharp stress-loss bounds',
        'nearest':['workflow-v15/c01','workflow-v15/c10'],
        'novelty':'Optimize over an undisclosed product-by-geography allocation constrained by two sets of authentic marginal totals. Finite revenue and gross-profit stress-loss endpoints must be feasible and sharp, rather than returning unresolved or multiplying a supplied forecast interval.',
        'request':'Assess Apple FY2024 revenue exposure to the authored regional demand stress in stress_rates. The source discloses worldwide Products and Services sales and costs, and country sales totals, but no joint sales table. Calculate exact worldwide gross profit and margins, feasible bounds on Products sales in each geography, and the tightest possible loss intervals for total revenue and gross profit under the stated scenario. Do not substitute proportional allocation for the missing joint sales disclosure.',
        'assumptions':'Authored sensitivity scenario, not an issuer forecast: allocate sales into nonnegative Products/Services by U.S., China (including Hong Kong and Taiwan), and other countries, preserving both sets of supplied totals. No other cross-cell constraints apply. The rates in stress_rates are percentage reductions of the relevant cell sales. Lost sales carry that business line\'s worldwide FY2024 gross margin in every geography. Beyond the cost-of-sales change implied by those margins, no secondary demand response, geographic switching or other profit changes occur. Gross profit here is sales less cost of sales. Optimize revenue and gross-profit loss separately over the same feasible allocations. Bounds are inclusive. The actual joint allocation is unknown.',
        'definitions':{
          'worldwide_mix':'Two rows keyed products and services. Report annual net sales, gross profit and gross margin percent.',
          'regional_product_bounds':'Three rows keyed us, china and other. Each interval is the sharp feasible bound on that geography\'s Products sales under the marginal totals and nonnegativity. Each endpoint may use its own feasible joint allocation.',
          'stress_bounds':'Two rows keyed revenue and gross_profit. Return sharp lower and upper total stress losses in USD million. lower_pct and upper_pct use original worldwide revenue and original worldwide gross profit respectively. These are bounds from allocation uncertainty, not a supplied forecast range. No particular witness allocation or explanatory wording is required. Optional prose is not semantically graded.'},
        'tables':{
          'worldwide_mix':spec([(x,'text' if x=='business_line' else 'pct' if x=='gross_margin_pct' else 'money') for x in ['business_line','net_sales_usd_million','gross_profit_usd_million','gross_margin_pct']],['business_line'],[['c01:s01']]),
          'regional_product_bounds':spec([(x,'text' if x=='geography' else 'money') for x in ['geography','lower_usd_million','upper_usd_million']],['geography'],[['c01:s01','c01:s02']]),
          'stress_bounds':spec([(x,'text' if x=='measure' else 'pct' if x.endswith('_pct') else 'money') for x in ['measure','lower_usd_million','upper_usd_million','lower_pct','upper_pct']],['measure'],[['c01:s01','c01:s02','c01:s04']])},
        'claims':{
          'claim_1':{'assertion':'The stated marginals and scenario identify one unique total gross-profit loss.','verdict':'contradicted','evidence':[['c01:s01','c01:s02','c01:s04']]},
          'claim_2':{'assertion':'Worldwide FY2024 Services gross margin exceeds worldwide Products gross margin.','verdict':'supported','evidence':[['c01:s01']]},
          'claim_3':{'assertion':'Products account for more than half of U.S. FY2024 sales.','verdict':'unresolved','evidence':[['c01:s01','c01:s02']]}}}}


def controls(key, original):
    """Coherent changed-input cases plus explicitly independent reported discrepancies."""
    out = []
    def add(name, rationale, mutate):
        data = copy.deepcopy(original)
        mutate(data)
        out.append((name,rationale,data))
    def scale(d):
        for table, values in d.items():
            if table == 'stress_rates':
                continue
            for row in values:
                for col, value in row.items():
                    if isinstance(value,(float,int)) and col!='year': row[col]=value*2
    add('monetary_scale','All monetary observations double, ratios and dimensionless bounds stay invariant.',scale)
    add('row_order','Reverse every input table. Logical financial results are unchanged.',lambda d:[v.reverse() for v in d.values()])
    if key=='a01':
        def quarter(d):
            d['quarter_current'][1]['calendar']+=80
            d['period_sales'][1]['fy2016']+=80
            d['group_annual'][1]['proforma']+=80
        add('calendar_extension','Extra comparable calendar sales enter current Q4 and annual pro forma equally. Pre-Q4 stays fixed.',quarter)
        def week(d):
            d['period_sales'][0]['q42015']+=100
            d['period_sales'][0]['fy2015']+=100
            d['group_annual'][0]['ifrs']+=100
            d['group_annual'][0]['proforma']+=100
        add('prior_extra_week','Extra-week sales change only unadjusted prior-period observations. Comparable amounts stay fixed.',week)
        def divest(d):
            d['quarter_current'][2]['divestments']-=20
            d['period_sales'][2]['fy2016']-=20
            d['group_annual'][1]['proforma']-=20
        add('divestment_scope','A further Q4 pro forma exclusion affects current annual pro forma equally. IFRS and pre-Q4 unchanged.',divest)
        def report(d): d['group_annual'][1]['proforma']+=7
        add('independent_reported_discrepancy','Synthetic independent group/segment disclosure discrepancy. Keep the residual, not force agreement.',report)
    elif key=='b01':
        def timing(d):
            d['cash_flows'][0]['cash_ppe']+=1000
            d['ppe'][1]['capital_payables_billion']-=1
        add('payable_settlement','Paying an extra 1000 reduces closing capital payables by 1000. Accrual proxy unchanged.',timing)
        def lease(d):
            d['annual_expenses'][0]['finance_rou_additions']+=500
            for t in ['ppe','finance_leases']:
                d[t][1]['gross']+=500
                d[t][1]['net']+=500
        add('noncash_lease','New lease recognition raises total and subset gross/net assets. Cash and residuals unchanged.',lease)
        def principal(d): d['annual_expenses'][0]['finance_principal_cash']+=100
        add('principal_settlement','Principal cash settlement changes defined cash outlay, not gross asset recognition. Lease liabilities are not supplied.',principal)
        def other(d): d['cash_flows'][0]['depreciation_amortization_other']+=800
        add('other_cf_adjustment','Unrelated other cash-flow adjustment changes, while Note 6 PPE depreciation stays fixed.',other)
        def residual(d):
            d['ppe'][1]['gross']+=250
            d['ppe'][1]['net']+=250
        add('unallocated_asset_movement','A synthetic noncash gross/net PPE movement is not assigned to a cause. The total-PPE residual increases.',residual)
    else:
        def regions(d):
            d['geographies'][1]['net_sales']+=70000
            d['geographies'][2]['net_sales']-=70000
        add('capacity_breakpoint','Move country sales from Other to China, preserving global totals. Optimal service allocation crosses a capacity boundary.',regions)
        def rates(d):
            d['stress_rates'][0]['products_loss_pct']=40
            d['stress_rates'][2]['services_loss_pct']=30
        add('slope_reversal','Change only authored stress rates, reversing allocation preference and allowing a negative marginal saving.',rates)
        def mix(d):
            d['business_lines'][0]['net_sales']-=80000
            d['business_lines'][1]['net_sales']+=80000
        add('product_mix','Move revenue from Products to Services with costs fixed, preserving global/geographic totals and nonnegative margins.',mix)
    return out


def alternatives(key):
    """Different valid formulations, including a greedy optimizer for the bounds case."""
    result = dict(specifications()[key]['sql'])
    if key=='a01':
        result['comparable_periods'] = result['comparable_periods'].replace(
            'fy2015-extra_week-q42015_matched', 'fy2015-q42015')
        result['quarter_scope'] = AHOLD_CTE+"""SELECT segment,current_q4 proforma_q42016_eur_million,
 q42015-q42015_matched extra_week2015_eur_million,current_q4-q42015_matched change_eur_million,
 100.0*(current_q4-q42015_matched)/q42015_matched growth_pct FROM q"""
    elif key=='b01':
        result['ppe_bridge'] = """WITH b AS (
 SELECT c.cash_ppe,a.*,1000.0*(p.capital_payables_billion-o.capital_payables_billion) pc,
 p.gross-o.gross dg,p.accumulated-o.accumulated da
 FROM cash_flows c JOIN annual_expenses a USING(year) JOIN ppe p USING(year) JOIN ppe o ON o.year=c.year-1)
 SELECT pc payables_change_usd_million,cash_ppe+pc purchase_proxy_usd_million,
 finance_rou_additions lease_additions_usd_million,1000.0*ppe_depreciation_billion depreciation_usd_million,
 dg-da net_change_usd_million,cash_ppe+pc+finance_rou_additions-1000.0*ppe_depreciation_billion explained_change_usd_million,
 (dg-cash_ppe-pc-finance_rou_additions)-(da-1000.0*ppe_depreciation_billion) residual_usd_million FROM b"""
        result['lease_movements'] = result['lease_movements'].replace('c.net-p.net net','(c.gross-p.gross)-(c.accumulated-p.accumulated) net')
    else:
        result['stress_bounds'] = APPLE_CTE+""", objectives AS (
 SELECT 'revenue' measure,1.0 pw,1.0 sw,p+s base,s FROM lines UNION ALL
 SELECT 'gross_profit',pm,sm,p*pm+s*sm,s FROM lines),
 slopes AS (SELECT o.*,r.geography,r.net_sales cap,r.pr*o.pw intercept,r.pr*o.pw-r.sr*o.sw slope
 FROM objectives o CROSS JOIN r),
 directions AS (SELECT 'lower' endpoint,-1 direction UNION ALL SELECT 'upper',1),
 ranked AS (SELECT slopes.*,d.endpoint,
 COALESCE(SUM(cap) OVER(PARTITION BY measure,d.endpoint ORDER BY d.direction*slope,geography
 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) used FROM slopes CROSS JOIN directions d),
 losses AS (SELECT measure,endpoint,base,SUM(cap*intercept-MAX(0,MIN(cap,s-used))*slope) loss
 FROM ranked GROUP BY measure,endpoint,base)
 SELECT measure,MAX(CASE WHEN endpoint='lower' THEN loss END) lower_usd_million,
 MAX(CASE WHEN endpoint='upper' THEN loss END) upper_usd_million,
 100.0*MAX(CASE WHEN endpoint='lower' THEN loss END)/base lower_pct,
 100.0*MAX(CASE WHEN endpoint='upper' THEN loss END)/base upper_pct FROM losses GROUP BY measure,base"""
    return result
