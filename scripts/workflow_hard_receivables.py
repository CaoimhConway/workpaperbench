"""Receivables-sale cash classification and retained-interest reconstruction."""
import copy
from decimal import Decimal


def d(value):
    return Decimal(str(value))


def calculate(data):
    flows = {r['period']: r for r in data['facility_flows']}
    policies = {r['period']: r['basis'] for r in data['facility_policy']}
    cash = sorted(data['cash_flows'], key=lambda r: r['sequence'])
    recast = []
    for row in cash:
        flow = flows.get(row['period'])
        customer = d(flow['dpp_collections']) if policies[row['period']] == 'sale' else d(0)
        principal = d(flow['purchaser_payment']) if policies[row['period']] == 'sale' else d(0)
        # Cash classification entries preserve the net change in treasury cash.
        amounts = {'operating': d(row['operating']), 'investing': d(row['investing']),
                   'financing': d(row['financing'])}
        for origin, destination, amount in [('investing','operating',customer),
                                             ('financing','investing',principal)]:
            amounts[origin] -= amount
            amounts[destination] += amount
        recast.append([row['period'], *[float(amounts[k]) for k in ['operating','investing','financing']],
                       float(sum(amounts.values()))])
    old, new = cash
    reported_change = d(new['operating']) - d(old['operating'])
    normalized_change = d(recast[1][1]) - d(recast[0][1])
    collateral_change = d(new['collateral']) - d(old['collateral'])
    capex_change = d(new['capex']) - d(old['capex'])
    changes = [reported_change, normalized_change, reported_change-normalized_change,
               collateral_change, normalized_change-collateral_change,
               normalized_change-capex_change, normalized_change-collateral_change-capex_change]
    opening, closing = sorted(data['facility_balances'], key=lambda r: r['sequence'])
    flow = next(r for r in data['facility_flows'] if r['period'] == old['period'])
    originations = d(flow['receivables_sold']) - d(flow['new_transfer_cash'])
    funding_change = d(closing['purchaser_funding']) - d(opening['purchaser_funding'])
    dpp_change = d(closing['dpp']) - d(opening['dpp'])
    explained = d(old['noncash_dpp']) - d(flow['dpp_collections']) - funding_change
    bridge = [originations, funding_change, dpp_change, explained, dpp_change-explained]
    return {'cashflow_recast': recast, 'cash_generation_change': [[float(v) for v in changes]],
            'retained_interest_bridge': [[old['period'], *[float(v) for v in bridge]]]}


BASE = """WITH recast AS (
 SELECT c.*,c.operating+CASE WHEN p.basis='sale' THEN f.dpp_collections ELSE 0 END operating_cash,
 c.investing-CASE WHEN p.basis='sale' THEN f.dpp_collections-f.purchaser_payment ELSE 0 END investing_cash,
 c.financing-CASE WHEN p.basis='sale' THEN f.purchaser_payment ELSE 0 END financing_cash
 FROM cash_flows c JOIN facility_policy p USING(period)
 LEFT JOIN facility_flows f USING(period)
) """
SQL = {
    'cashflow_recast': BASE + """SELECT period,operating_cash,investing_cash,financing_cash,
 operating_cash+investing_cash+financing_cash total_cash FROM recast""",
    'cash_generation_change': BASE + """, changes AS (
 SELECT n.operating-o.operating reported_operating_change,
 n.operating_cash-o.operating_cash normalized_operating_change,
 n.collateral-o.collateral collateral_change,n.capex-o.capex capex_change
 FROM recast o JOIN recast n ON n.sequence=o.sequence+1
) SELECT reported_operating_change,normalized_operating_change,
 reported_operating_change-normalized_operating_change presentation_effect,
 collateral_change,normalized_operating_change-collateral_change other_operating_change,
 normalized_operating_change-capex_change normalized_after_capex_change,
 normalized_operating_change-collateral_change-capex_change other_after_capex_change
 FROM changes""",
    'retained_interest_bridge': """WITH movements AS (
 SELECT f.period,f.receivables_sold-f.new_transfer_cash new_dpp_from_transfers,
 e.purchaser_funding-b.purchaser_funding funding_change,e.dpp-b.dpp reported_dpp_change,
 c.noncash_dpp-f.dpp_collections-(e.purchaser_funding-b.purchaser_funding) explained_dpp_change
 FROM cash_flows c JOIN facility_flows f USING(period)
 CROSS JOIN facility_balances b JOIN facility_balances e ON e.sequence=b.sequence+1
) SELECT *,reported_dpp_change-explained_dpp_change unallocated_dpp_change FROM movements""",
}


def alternatives():
    """Cash-journal pivot and receivable-pool roll-forward are alternate models."""
    journal = """WITH journal AS (
 SELECT period,'operating' category,operating amount FROM cash_flows
 UNION ALL SELECT period,'investing',investing FROM cash_flows
 UNION ALL SELECT period,'financing',financing FROM cash_flows
 UNION ALL SELECT f.period,'operating',f.dpp_collections FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
 UNION ALL SELECT f.period,'investing',-f.dpp_collections FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
 UNION ALL SELECT f.period,'investing',f.purchaser_payment FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
 UNION ALL SELECT f.period,'financing',-f.purchaser_payment FROM facility_flows f
 JOIN facility_policy p USING(period) WHERE p.basis='sale'
), recast AS (
 SELECT c.*,SUM(CASE WHEN category='operating' THEN amount ELSE 0 END) operating_cash,
 SUM(CASE WHEN category='investing' THEN amount ELSE 0 END) investing_cash,
 SUM(CASE WHEN category='financing' THEN amount ELSE 0 END) financing_cash
 FROM cash_flows c JOIN journal j USING(period) GROUP BY c.period
) """
    result = {name: query.replace(BASE, journal) for name, query in SQL.items()}
    result['retained_interest_bridge'] = """WITH pool AS (
 SELECT f.period,f.receivables_sold-f.new_transfer_cash new_dpp_from_transfers,
 e.purchaser_funding-b.purchaser_funding funding_change,
 (e.pool_fair_value-e.purchaser_funding)-(b.pool_fair_value-b.purchaser_funding) reported_dpp_change,
 f.receivables_sold-f.cash_reinvested-(e.purchaser_funding-b.purchaser_funding) explained_dpp_change
 FROM facility_flows f CROSS JOIN facility_balances b
 JOIN facility_balances e ON e.sequence=b.sequence+1
) SELECT *,reported_dpp_change-explained_dpp_change unallocated_dpp_change FROM pool"""
    return result


def declaration(columns, keys, evidence):
    return {'columns':{name:({'type':'text','unit':'label'} if unit=='label' else
                            {'type':'real','unit':unit,'tolerance':1e-6}) for name,unit in columns},
            'keys':keys,'row_order':'ignored','duplicates':'Keys must be unique',
            'evidence':evidence,'context_evidence_allowed':[]}


def specification():
    cash_support = [['c01:s01','c01:s02','c01:s03','c01:s07'],
                    ['c01:s01','c01:s02','c01:s07']]
    bridge_support = [['c01:s01','c01:s02','c01:s05','c01:s07'],
                      ['c01:s02','c01:s05','c01:s07']]
    return {
        'source':'constellation-2025','calculate':calculate,'sql':SQL,
        'title':'Customer collections through a receivables-financing transition',
        'nearest':['workflow-v15/a07','workflow-v15/b10','workflow-v15/c07','workflow-hard-pilot-v1/b01'],
        'novelty':'Construct a consistent cash classification across receivables sales with retained interests and secured borrowing. Separate customer receipts, recycled transfer proceeds, net purchaser funding and noncash retained-interest creation, then preserve the stock-flow residual.',
        'request':'Assess whether Constellation Energy Corporation consolidated cash generation improved in the nine months ended September 30, 2025 relative to the same 2024 period. Present both periods on a consistent NER-facility basis with customer collections in operating activities and purchaser principal cash in financing activities. Reconstruct the operating, investing and financing totals, quantify the change with and without collateral cash, and reconcile the 2024 retained-interest movement from its disclosures. Keep separate tariff receivables sales within their reported treatment.',
        'assumptions':'Authored analytical presentation: adjust only the NER facility to put customer collection cash in operating activities and net purchaser principal cash in financing activities for both periods. This is an analytical presentation, not a correction of the issuer\'s GAAP statements. Other cash flows retain their reported classifications. Ignore no actual cash item, and do not invent collections or timing benefits for separate tariff receivables sales. Compare the CEG Parent consolidated group, not the separately presented Generation LLC group. Cash after capex means cash remaining after the reported capital expenditure payments, without changing any other investing activity. Collateral-neutral measures exclude only the signed Collateral received (posted), net operating line. These definitions do not establish sustainable or companywide financing-free cash generation.',
        'definitions':{
            'cashflow_recast':'One row per cash-flow period, with operating_cash, investing_cash, financing_cash and total_cash in USD million. Preserve the observed total cash movement while constructing the NER-consistent classification.',
            'cash_generation_change':'One row with 2025 nine-month amounts minus 2024 nine-month amounts, all USD million. reported_operating_change uses reported CFO. normalized_operating_change uses the NER-consistent CFO. presentation_effect is the portion of the reported change caused by this difference in presentation. collateral_change is the signed collateral cash change. other_operating_change excludes that collateral contribution from the NER-consistent change. normalized_after_capex_change and other_after_capex_change apply the respective bases after capex. The remaining other change is not assigned a cause.',
            'retained_interest_bridge':'One row for 2024-9m, all amounts USD million. new_dpp_from_transfers is the retained consideration implied by receivables transferred and cash proceeds. funding_change is closing less opening purchaser funding. reported_dpp_change is closing less opening DPP. explained_dpp_change is the retained-interest movement explained by the supplied period transactions and funding structure. unallocated_dpp_change is reported movement less the explained movement. Preserve the net residual without assigning it a specific cause.'},
        'tables':{
            'cashflow_recast':declaration([('period','label'),('operating_cash','usd_million'),('investing_cash','usd_million'),('financing_cash','usd_million'),('total_cash','usd_million')],['period'],cash_support),
            'cash_generation_change':declaration([(k,'usd_million') for k in ['reported_operating_change','normalized_operating_change','presentation_effect','collateral_change','other_operating_change','normalized_after_capex_change','other_after_capex_change']],[],cash_support),
            'retained_interest_bridge':declaration([('period','label')]+[(k,'usd_million') for k in ['new_dpp_from_transfers','funding_change','reported_dpp_change','explained_dpp_change','unallocated_dpp_change']],['period'],bridge_support)},
        'claims':{
            'claim_1':{'assertion':'On the NER-consistent presentation, operating cash generation increased in the nine months ended September 30, 2025 versus the same 2024 period.','verdict':'contradicted','evidence':cash_support},
            'claim_2':{'assertion':'The NER-consistent presentation preserves the reported 2024 nine-month increase in cash, restricted cash and cash equivalents.','verdict':'supported','evidence':cash_support+[['c01:s01','c01:s07']]},
            'claim_3':{'assertion':'Separate tariff receivables sales had no cash-timing benefit in the 2025 nine-month period.','verdict':'unresolved','evidence':[['c01:s04'],['c01:s03','c01:s04','c01:s07']]}}
    }


def controls(original):
    out = []
    def add(name, rationale, mutation):
        data = copy.deepcopy(original)
        mutation(data)
        out.append((name,rationale,data))
    def scale(data):
        for rows in data.values():
            for row in rows:
                for key,value in row.items():
                    if isinstance(value,(int,float)) and key!='sequence':
                        row[key] *= 2
    add('scale','Double all monetary observations while preserving periods and classifications.',scale)
    add('row_order','Reverse rows without changing dates or sequence identities.',lambda data:[rows.reverse() for rows in data.values()])
    def collection(data):
        f = data['facility_flows'][0]
        f['dpp_collections'] += 100
        f['cash_reinvested'] += 100
        c = next(r for r in data['cash_flows'] if r['period']==f['period'])
        for k in ['investing','net_cash_change','net_dpp_investing']:
            c[k] += 100
        for k in ['dpp','pool_fair_value']:
            data['facility_balances'][1][k] -= 100
    add('customer_collection','A further customer collection reduces retained receivables and raises old-basis investing cash. Funding is unchanged.',collection)
    def funding(data):
        data['facility_flows'][0]['purchaser_payment'] = -200
        data['facility_balances'][1]['purchaser_funding'] = 500
        data['facility_balances'][1]['dpp'] -= 500
        c = data['cash_flows'][0]
        for k in ['investing','net_cash_change','net_dpp_investing']:
            c[k] += 500
    add('funding_draw','Replace the 300 principal repayment with a 200 net funding receipt. Closing purchaser funding becomes 500 and DPP falls by 500. Customer collections do not change.',funding)
    def origin(data):
        data['facility_flows'][0]['receivables_sold'] += 250
        data['cash_flows'][0]['noncash_dpp'] += 250
        for k in ['dpp','pool_fair_value']:
            data['facility_balances'][1][k] += 250
    add('noncash_originations','Additional receivables are transferred entirely for retained consideration. They increase the DPP asset without changing any cash flow.',origin)
    def valuation(data):
        for k in ['dpp','pool_fair_value']:
            data['facility_balances'][1][k] += 20
    add('unallocated_movement','A synthetic additional fair-value movement increases the pool and retained interest without cash. It changes the unexplained residual.',valuation)
    def collateral(data):
        c = data['cash_flows'][1]
        for k in ['operating','net_cash_change','collateral']:
            c[k] += 100
    add('collateral_cash','Reduce collateral cash posted in 2025 by 100, increasing reported cash. The collateral-neutral change remains invariant.',collateral)
    def capex(data):
        c = data['cash_flows'][1]
        c['capex'] += 50
        c['investing'] -= 50
        c['net_cash_change'] -= 50
    add('capex_cash','An additional 50 capital expenditure payment changes cash after capex but not operating cash generation.',capex)
    return out


def mistakes():
    return {
        'net_dpp_as_collections':{'table':'cashflow_recast','sql':SQL['cashflow_recast'].replace('f.dpp_collections','c.net_dpp_investing').replace('f.purchaser_payment','0.0'),
                                'rationale':'The net investing line includes purchaser principal repayment, so it is not gross customer DPP collections.'},
        'double_count_recycling':{'table':'cashflow_recast','sql':SQL['cashflow_recast'].replace('THEN f.dpp_collections ELSE','THEN f.dpp_collections+f.new_transfer_cash ELSE'),
                                'rationale':'Transfer proceeds were already recognized in reported operating cash and the reinvested total is not a further cash receipt.'},
        'noncash_dpp_as_cash':{'table':'cashflow_recast','sql':SQL['cashflow_recast'].replace('c.operating+CASE','c.operating+c.noncash_dpp+CASE'),
                              'rationale':'A newly retained purchase-price asset is not cash generation.'},
        'principal_sign':{'table':'cashflow_recast','sql':SQL['cashflow_recast'].replace('c.financing-CASE','c.financing+CASE'),
                          'rationale':'A payment reducing purchaser funding is a financing outflow on the requested presentation.'},
        'gross_reassignment_cash':{'table':'cashflow_recast','sql':SQL['cashflow_recast'].replace('c.operating+CASE','c.operating+(SELECT dpp_reassigned FROM transition)+CASE'),
                                  'rationale':'The reassignment exchanges two assets and is outside the prior nine-month period.'},
        'funding_omitted_from_dpp':{'table':'retained_interest_bridge','sql':SQL['retained_interest_bridge'].replace('c.noncash_dpp-f.dpp_collections-(e.purchaser_funding-b.purchaser_funding)','c.noncash_dpp-f.dpp_collections'),
                                  'rationale':'Paying down purchaser funding increases the retained interest without collecting a customer invoice.'},
        'force_zero_residual':{'table':'retained_interest_bridge','sql':SQL['retained_interest_bridge'].replace('reported_dpp_change-explained_dpp_change unallocated_dpp_change','0.0 unallocated_dpp_change'),
                               'rationale':'The source stock and flow observations leave a nonzero unexplained movement.'},
        'loss_as_residual':{'table':'retained_interest_bridge','sql':SQL['retained_interest_bridge'].replace('reported_dpp_change-explained_dpp_change unallocated_dpp_change','-(SELECT loss_on_sale FROM credit_losses) unallocated_dpp_change'),
                            'rationale':'A separately reported loss on sales is not a complete retained-interest fair-value roll-forward.'},
    }
