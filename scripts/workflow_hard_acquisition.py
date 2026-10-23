"""Acquisition accounting, cash classification and performance-basis case."""
import copy
from decimal import Decimal

D = lambda value: Decimal(str(value))


def calculate(data):
    deals, cash_rows = [], []
    by_year = {}
    for row in data['acquisitions']:
        cash = D(row['cash_shares']) + D(row['cash_awards'])
        noncash = sum(D(row[k]) for k in ('share_consideration','cvr_common','replacement_options','replacement_rsus','cvr_awards'))
        compensation = D(row['unvested_award_charge'])
        basis = cash + noncash if row['method']=='business_combination' else cash-compensation+D(row['transaction_costs'])
        net = cash-D(row['cash_acquired'])
        disposal = D(row['required_disposal'])
        deals.append([row['deal'],float(basis),float(basis-D(row['reported_basis'])),float(noncash),
                      float(net),float(net-compensation),float(net-disposal)])
        by_year[row['year']] = (compensation,net-compensation,disposal)
    periods={row['year']:row for row in data['periods']}
    for year,row in periods.items():
        compensation, acquisition, disposal=by_year[year]
        other_acquisitions=D(row['acquisition_payments'])-acquisition
        other_disposals=D(row['divestiture_proceeds'])-disposal
        remaining=D(row['operating_cash'])-D(row['capex'])-D(row['acquisition_payments'])+D(row['divestiture_proceeds'])
        cash_rows.append([year,float(D(row['operating_cash'])+compensation),float(acquisition),
                          float(other_acquisitions),float(other_disposals),float(remaining)])
    current=periods[2020]
    prior=periods[2019]
    proforma=next(r for r in data['proforma_revenue'] if r['year']==2019)
    effect=next(r for r in data['acquisition_effects'] if r['deal']=='MyoKardia')
    immediate=sum(D(effect[k]) for k in ('iprd_charge','sales_admin_award_charge','research_award_charge'))
    neutral=D(current['pretax'])+immediate+D(current['contingent_fv_expense'])
    views=[['reported_revenue_growth_percent',float((D(current['revenue'])/D(prior['revenue'])-1)*100)],
           ['proforma_baseline_revenue_growth_percent',float((D(current['revenue'])/D(proforma['revenue'])-1)*100)],
           ['immediate_myokardia_expenses_usd_million',float(immediate)],
           ['selected_effects_excluded_pretax_usd_million',float(neutral)]]
    return {'acquisition_bases':deals,'cash_coverage':cash_rows,'performance_views':views}


BASE="""WITH amounts AS (
 SELECT *,cash_shares+cash_awards cash,
 share_consideration+cvr_common+replacement_options+replacement_rsus+cvr_awards noncash
 FROM acquisitions
), deals AS (
 SELECT *,cash-cash_acquired net_cash,
 CASE WHEN method='business_combination' THEN cash+noncash
 ELSE cash-unvested_award_charge+transaction_costs END basis FROM amounts
) """
SQL={
'acquisition_bases':BASE+"""SELECT deal,basis accounting_basis_usd_million,
 basis-reported_basis reported_basis_residual_usd_million,noncash noncash_consideration_usd_million,
 net_cash net_cash_paid_usd_million,
 net_cash-unvested_award_charge noncompensation_net_cash_usd_million,
 net_cash-required_disposal post_disposal_net_cash_usd_million FROM deals""",
'cash_coverage':BASE+"""SELECT p.year,p.operating_cash+d.unvested_award_charge operating_cash_before_deal_compensation_usd_million,
 d.net_cash-d.unvested_award_charge identified_noncompensation_cash_usd_million,
 p.acquisition_payments-(d.net_cash-d.unvested_award_charge) other_acquisition_cash_usd_million,
 p.divestiture_proceeds-d.required_disposal other_divestiture_cash_usd_million,
 p.operating_cash-p.capex-p.acquisition_payments+p.divestiture_proceeds cash_after_portfolio_investment_usd_million
 FROM periods p JOIN deals d USING(year)""",
'performance_views':"""WITH current AS (SELECT * FROM periods WHERE year=2020),
 prior AS (SELECT * FROM periods WHERE year=2019),
 comparable AS (SELECT * FROM proforma_revenue WHERE year=2019),
 charges AS (SELECT iprd_charge+sales_admin_award_charge+research_award_charge amount
 FROM acquisition_effects WHERE deal='MyoKardia')
 SELECT 'reported_revenue_growth_percent' measure,(c.revenue/p.revenue-1)*100 value FROM current c CROSS JOIN prior p
 UNION ALL SELECT 'proforma_baseline_revenue_growth_percent',(c.revenue/p.revenue-1)*100 FROM current c CROSS JOIN comparable p
 UNION ALL SELECT 'immediate_myokardia_expenses_usd_million',amount FROM charges
 UNION ALL SELECT 'selected_effects_excluded_pretax_usd_million',pretax+amount+contingent_fv_expense
 FROM current CROSS JOIN charges"""}


def alternatives():
    result=dict(SQL)
    # Asset-allocation identity independently establishes the accounting basis.
    result['acquisition_bases']=BASE+""", asset_basis AS (
 SELECT deal,SUM(amount) basis FROM allocated_assets GROUP BY deal
) SELECT d.deal,a.basis accounting_basis_usd_million,
 a.basis-d.reported_basis reported_basis_residual_usd_million,d.noncash noncash_consideration_usd_million,
 d.net_cash net_cash_paid_usd_million,
 d.net_cash-d.unvested_award_charge noncompensation_net_cash_usd_million,
 d.net_cash-d.required_disposal post_disposal_net_cash_usd_million
 FROM deals d JOIN asset_basis a USING(deal)"""
    # Rebuild the same cash remainder from compensation-neutral CFO and deal cash.
    result['cash_coverage']=BASE+""", bridge AS (
 SELECT p.*,d.unvested_award_charge compensation,d.net_cash,d.required_disposal,
 p.acquisition_payments-d.net_cash+d.unvested_award_charge other_acquisitions,
 p.divestiture_proceeds-d.required_disposal other_disposals
 FROM periods p JOIN deals d USING(year)
) SELECT year,operating_cash+compensation operating_cash_before_deal_compensation_usd_million,
 net_cash-compensation identified_noncompensation_cash_usd_million,
 other_acquisitions other_acquisition_cash_usd_million,other_disposals other_divestiture_cash_usd_million,
 operating_cash+compensation-capex-net_cash-other_acquisitions+required_disposal+other_disposals
 cash_after_portfolio_investment_usd_million FROM bridge"""
    result['performance_views'] = SQL['performance_views'].split("UNION ALL SELECT 'selected_effects_excluded_pretax_usd_million'")[0] + """UNION ALL
 SELECT 'selected_effects_excluded_pretax_usd_million',
 SUM(CASE l.line WHEN 'revenue' THEN l.amount WHEN 'iprd' THEN 0
 WHEN 'sales_admin' THEN -(l.amount-e.sales_admin_award_charge)
 WHEN 'research' THEN -(l.amount-e.research_award_charge)
 WHEN 'other_expense' THEN -(l.amount-p.contingent_fv_expense)
 ELSE -l.amount END)
 FROM earnings_lines l JOIN periods p USING(year)
 JOIN acquisition_effects e USING(year) WHERE l.year=2020"""
    return result


def declaration(columns,keys,evidence,context=()):
    return {'columns':{name:({'type':'text','unit':'label'} if kind=='label' else
                            {'type':'integer','unit':'year'} if kind=='year' else
                            {'type':'real','unit':kind,'tolerance':1e-7}) for name,kind in columns},
            'keys':keys,'row_order':'ignored','duplicates':'Keys must be unique',
            'evidence':evidence,'context_evidence_allowed':list(context)}


def specification():
    bases=[['b01:s01','b01:s02','b01:s07','b01:s08']]
    cash=[['b01:s01','b01:s02','b01:s03','b01:s04','b01:s07','b01:s08']]
    performance=[['b01:s02','b01:s05','b01:s06','b01:s08'],['b01:s02','b01:s03','b01:s05','b01:s06','b01:s08']]
    return {
      'source':'bms-2020','calculate':calculate,'sql':SQL,
      'title':'BMS acquisition costs, cash funding and performance bases',
      'nearest':['workflow-v15/c07','workflow-hard-pilot-v1/a01','workflow-hard-pilot-v1/b01'],
      'novelty':'Distinguish business-combination consideration from asset-acquisition cost and cash paid, separate cash compensation embedded in a transaction, and connect those classifications to company operating and investing cash without counting the same payment twice. Compare revenue on a disclosed acquisition/divestiture perimeter while keeping an explicitly limited earnings diagnostic separate.',
      'request':'Assess the Celgene/Otezla and MyoKardia transactions using BMS consolidated FY2020 disclosures. Reconstruct accounting acquisition bases and disclosed transaction cash, reconcile their cash-payment components with the company cash-flow statements for 2019 and 2020, and evaluate the specified revenue and pretax-earnings views. All amounts are USD million except percentages. Use the finalized Celgene allocation in this filing.',
      'assumptions':[
        'Deal cash metrics cover only the listed cash consideration and acquired cash, with Otezla as the sole specified required divestiture. They exclude transaction fees, financing flows and taxes. The source does not establish cash payment timing for the capitalized MyoKardia transaction costs. Do not infer that accounting cost is a cash payment.',
        'The disclosed transaction-cost amounts retain their source accounting bases: Celgene acquisition expenses and MyoKardia costs included in asset allocation. Zero components in acquisitions are structurally absent from the listed consideration, not a claim that every other possible transaction cash flow was zero.',
        'For cash_coverage, retain the reported operating cash and investing-category totals. Do not attempt to allocate the remaining acquisition/other payments to individual undisclosed fees or other transactions. Equity and debt financing and marketable-security turnover are outside the requested cash remainder.',
        'The earnings diagnostic excludes only acquisition-date MyoKardia expenses and all contingent-consideration fair-value changes in 2020. Keep other income-statement items unchanged and make no tax adjustment. It is not issuer non-GAAP earnings or a fully normalized continuing-business result.',
        'The revenue comparison uses actual 2020 revenue and the supplied 2019 Celgene/Otezla pro forma baseline. It does not assert constant currency, organic growth or a forecast. Source pro forma qualifications remain applicable.'
      ],
      'definitions':{
        'acquisition_bases':'One row per deal. accounting_basis is consideration transferred for the business combination or cost allocated for the asset acquisition. reported_basis_residual is reconstructed basis less its independently reported total. noncash_consideration is the fair value of listed consideration not paid in cash at closing. net_cash_paid is listed cash paid less cash acquired. noncompensation_net_cash excludes cash paid for compensation from that net cash. post_disposal_net_cash deducts the specified required divestiture from net_cash_paid. These cash metrics exclude fees, taxes and financing.',
        'cash_coverage':'One row per year. operating_cash_before_deal_compensation removes the cash effect of compensation contained in that year\'s listed acquisition payments from reported operating cash. identified_noncompensation_cash is the listed acquisition consideration, net of acquired cash, outside compensation. other_acquisition_cash is reported acquisition/other investing payments less that identified amount. other_divestiture_cash is reported divestiture/other proceeds less the specified required divestiture. cash_after_portfolio_investment is operating cash remaining after capital expenditure and the reported net acquisition/other and divestiture/other investing flows, excluding securities turnover and financing. Positive amounts mean cash available, negative amounts mean cash absorbed beyond operating generation.',
        'performance_views':'Four measure rows. reported_revenue_growth_percent compares actual 2020 with actual 2019. proforma_baseline_revenue_growth_percent compares actual 2020 with the supplied 2019 pro forma revenue. immediate_myokardia_expenses_usd_million is the acquisition-date expense recognized from that transaction. selected_effects_excluded_pretax_usd_million is 2020 reported pretax earnings with the two specified classes of effect excluded. A percentage measure uses percent units, the other two measures use USD million.'
      },
      'tables':{
        'acquisition_bases':declaration([('deal','label'),('accounting_basis_usd_million','usd_million'),('reported_basis_residual_usd_million','usd_million'),('noncash_consideration_usd_million','usd_million'),('net_cash_paid_usd_million','usd_million'),('noncompensation_net_cash_usd_million','usd_million'),('post_disposal_net_cash_usd_million','usd_million')],['deal'],bases,['b01:s03','b01:s04','b01:s09']),
        'cash_coverage':declaration([('year','year'),('operating_cash_before_deal_compensation_usd_million','usd_million'),('identified_noncompensation_cash_usd_million','usd_million'),('other_acquisition_cash_usd_million','usd_million'),('other_divestiture_cash_usd_million','usd_million'),('cash_after_portfolio_investment_usd_million','usd_million')],['year'],cash,['b01:s05','b01:s09']),
        'performance_views':declaration([('measure','label'),('value','measure_dependent')],['measure'],performance,['b01:s01','b01:s04','b01:s07'])
      },
      'claims':{
        'claim_1':{'assertion':'MyoKardia\'s reported allocation cost equals the listed cash consideration net of cash acquired.','verdict':'contradicted','evidence':[['b01:s02']]},
        'claim_2':{'assertion':'The Otezla disposal generated cash proceeds without a reported pretax divestiture gain.','verdict':'supported','evidence':[['b01:s07']]},
        'claim_3':{'assertion':'BMS organic revenue growth in 2020 exceeded six percent.','verdict':'unresolved','evidence':[['b01:s06','b01:s08'],['b01:s06'],['b01:s08']]}
      }
    }


def controls(data):
    out=[]
    def add(name,reason,edit):
        changed=copy.deepcopy(data)
        edit(changed)
        out.append((name,reason,changed))
    def amount(data,deal,component,change):
        next(r for r in data['allocated_assets'] if r['deal']==deal and r['component']==component)['amount']+=change
    def line(data,name,change):
        next(r for r in data['earnings_lines'] if r['line']==name)['amount']+=change
    def award(data):
        a=next(r for r in data['acquisitions'] if r['deal']=='MyoKardia')
        a['unvested_award_charge']+=118
        a['reported_basis']-=118
        p=next(r for r in data['periods'] if r['year']==2020)
        p['operating_cash']-=118
        p['acquisition_payments']-=118
        # Reallocate the same closing cash between compensation and asset cost.
        e=data['acquisition_effects'][0]
        e['sales_admin_award_charge']+=59
        e['research_award_charge']+=59
        e['iprd_charge']-=118
        amount(data,'MyoKardia','iprd',-118)
        line(data,'iprd',-118)
        line(data,'sales_admin',59)
        line(data,'research',59)
    add('compensation_classification','A greater portion of unchanged closing cash settles unvested service awards. Investing cash and asset cost fall as operating compensation rises. Total cash and immediate expense remain unchanged.',award)
    def cash_acquired(data):
        a=next(r for r in data['acquisitions'] if r['deal']=='Celgene')
        a['cash_acquired']+=200
        amount(data,'Celgene','cash',200)
        amount(data,'Celgene','goodwill',-200)
        next(r for r in data['periods'] if r['year']==2019)['acquisition_payments']-=200
    add('acquired_cash','More acquired cash offsets goodwill and reduces net investing cash without changing consideration.',cash_acquired)
    def fees(data):
        a=next(r for r in data['acquisitions'] if r['deal']=='MyoKardia')
        a['transaction_costs']+=20
        a['reported_basis']+=20
        amount(data,'MyoKardia','iprd',20)
        data['acquisition_effects'][0]['iprd_charge']+=20
        next(r for r in data['periods'] if r['year']==2020)['pretax']-=20
        line(data,'iprd',20)
    add('accrued_transaction_cost','Additional unpaid acquisition costs are allocated to IPRD and expensed. They change cost and earnings, with no new cash payment.',fees)
    def noncash(data):
        a=next(r for r in data['acquisitions'] if r['deal']=='Celgene')
        a['share_consideration']+=500
        a['reported_basis']+=500
        amount(data,'Celgene','goodwill',500)
    add('share_valuation','A higher closing value for issued shares raises consideration and goodwill but not closing cash.',noncash)
    def fairvalue(data):
        p=next(r for r in data['periods'] if r['year']==2020)
        p['contingent_fv_expense']+=300
        p['pretax']-=300
        line(data,'other_expense',300)
    add('noncash_remeasurement','A smaller noncash fair-value gain reduces reported earnings while the selected-effects diagnostic and cash remain invariant.',fairvalue)
    add('reported_total','An independent source-total discrepancy must remain visible in the stated residual.',lambda d:d['acquisitions'][0].update(reported_basis=d['acquisitions'][0]['reported_basis']+40))
    add('preacquisition_revenue','Additional prior-year target revenue before the actual acquisition date changes the pro forma comparator without changing statutory BMS revenue.',lambda d:next(r for r in d['proforma_revenue'] if r['year']==2019).update(revenue=40259))
    def current_revenue(data):
        next(r for r in data['periods'] if r['year']==2020)['revenue']+=1000
        line(data,'revenue',1000)
        line(data,'cost_of_products',1000)
    add('current_revenue','Incremental zero-margin current-year sales change both revenue comparisons while pretax earnings and cash are unchanged.',current_revenue)
    def scale(data):
        for table,rows in data.items():
            for row in rows:
                for key,value in row.items():
                    if isinstance(value,(int,float)) and key!='year':row[key]=value*2
    add('monetary_scale','Scale all monetary observations together. Growth percentages remain invariant.',scale)
    add('row_order','Input row order has no financial meaning.',lambda d:[v.reverse() for v in d.values()])
    return out


def mistakes():
    def replace(table,old,new,reason):
        assert old in SQL[table]
        return {'table':table,'sql':SQL[table].replace(old,new),'rationale':reason}
    return {
      'book_cost_as_cash':replace('acquisition_bases','net_cash net_cash_paid_usd_million','basis net_cash_paid_usd_million','Accounting cost includes noncash consideration and differs from cash net of acquired balances.'),
      'all_awards_compensation':replace('acquisition_bases','net_cash-unvested_award_charge noncompensation_net_cash_usd_million','net_cash-cash_awards noncompensation_net_cash_usd_million','Only the disclosed service-related award amount is compensation.'),
      'fees_as_paid_cash':replace('acquisition_bases','net_cash net_cash_paid_usd_million','net_cash+transaction_costs net_cash_paid_usd_million','The filing does not establish that the accounting transaction-cost amounts were paid at closing.'),
      'double_count_compensation':replace('cash_coverage','d.net_cash-d.unvested_award_charge','d.net_cash','This includes cash compensation already reflected in operating cash among acquisition investing payments.'),
      'expensed_iprd_is_operating_cash':replace('cash_coverage','p.operating_cash-p.capex-p.acquisition_payments','p.operating_cash-COALESCE((SELECT iprd_charge FROM acquisition_effects WHERE year=p.year),0)-p.capex-p.acquisition_payments','The IPRD expense is explicitly added back in operating cash. Acquisition investing cash is already included separately.'),
      'statutory_proforma_baseline':replace('performance_views','SELECT * FROM proforma_revenue WHERE year=2019','SELECT * FROM periods WHERE year=2019','The partial-period statutory comparator is not the supplied full-year acquisition/divestiture perimeter.'),
      'ignore_award_expense':replace('performance_views','iprd_charge+sales_admin_award_charge+research_award_charge amount','iprd_charge amount','MyoKardia acquisition-date expense also includes the cash-settled unvested awards.'),
      'remeasurement_sign':replace('performance_views','pretax+amount+contingent_fv_expense','pretax+amount-contingent_fv_expense','Excluding a fair-value gain reduces pretax earnings. It does not add the gain again.')}
