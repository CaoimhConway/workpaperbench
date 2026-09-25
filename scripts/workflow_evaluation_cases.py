"""Source-specific work products and independent held-out reference calculations."""
import copy
from decimal import Decimal

from build_workflow_tasks import TEXT, numeric, table
from workflow_development_cases import claim

D=lambda value:Decimal(str(value))
M=numeric('usd_million',0.001)
K=numeric('usd_thousand',0.001)
P=numeric('percent')


def circle_reference(data):
    expense=data['expense_reconciliation']
    periods=['FY2024','FY2025','Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025']
    facts={(r['period'],r['measure']):D(r['amount_usd_thousand']) for r in expense}
    model=[]
    for period in periods+['9MFY2024','9MFY2025']:
        def value(measure):
            if period.startswith('9M'):
                year=period[2:]
                return facts[year,measure]-facts['Q4'+year,measure]
            return facts[period,measure]
        def adjustments(group):
            if period.startswith('9M'):
                year=period[2:]
                return sum((D(r['amount_usd_thousand'])*(1 if r['period']==year else -1)
                    for r in expense if r['group_name']==group and r['period'] in (year,'Q4'+year)),D(0))
            return sum((D(r['amount_usd_thousand']) for r in expense if r['group_name']==group and r['period']==period),D(0))
        gaap,prior,new=value('gaap'),value('prior_definition'),value('new_definition')
        initial,extra=adjustments('prior_adjustment'),adjustments('extra_adjustment')
        model.append([period,float(gaap),float(gaap+initial),float(gaap+initial+extra),float(-extra),
                      float(gaap+initial-prior),float(gaap+initial+extra-new)])
    operations={(r['period'],r['measure']):D(r['amount_usd_thousand']) for r in data['operations']}
    margins=[]
    for period in ('FY2024','FY2025','Q4FY2024','Q4FY2025'):
        f=lambda measure:operations[period,measure]
        revenue=f('reserve_income')+f('other_revenue')
        cost=f('distribution')+f('other_costs')
        rldc=revenue-cost
        margins.append([period,float(revenue),float(rldc),float(100*rldc/revenue),float(100*f('adjusted_ebitda')/rldc),
                        float(revenue-f('total_revenue')),float(cost-f('total_costs'))])
    gap_change=(facts['FY2025','prior_definition']-facts['FY2025','new_definition'])-(facts['FY2024','prior_definition']-facts['FY2024','new_definition'])
    attribution=[]
    for measure in ('payroll_tax','legal','acquisition','restructuring'):
        before=-facts['FY2024',measure]
        after=-facts['FY2025',measure]
        attribution.append([measure,float(before),float(after),float(after-before),float(100*(after-before)/gap_change)])
    return {'expense_model':model,'operating_margins':margins,'definition_attribution':attribution}


CIRCLE_EXPENSE_SQL="""WITH p AS (SELECT period,
MAX(CASE WHEN measure='gaap' THEN amount_usd_thousand END) g,
SUM(CASE WHEN group_name='prior_adjustment' THEN amount_usd_thousand ELSE 0 END) a,
SUM(CASE WHEN group_name='extra_adjustment' THEN amount_usd_thousand ELSE 0 END) e,
MAX(CASE WHEN measure='prior_definition' THEN amount_usd_thousand END) old,
MAX(CASE WHEN measure='new_definition' THEN amount_usd_thousand END) new
FROM expense_reconciliation WHERE period IN ('FY2024','FY2025','Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025') GROUP BY period),
all_periods AS (SELECT * FROM p UNION ALL SELECT '9M'||a.period,a.g-q.g,a.a-q.a,a.e-q.e,a.old-q.old,a.new-q.new
FROM p a JOIN p q ON q.period='Q4'||a.period WHERE a.period IN ('FY2024','FY2025'))
SELECT period,g gaap_expense_usd_thousand,g+a prior_adjusted_usd_thousand,g+a+e new_adjusted_usd_thousand,
-e additional_exclusions_usd_thousand,g+a-old prior_residual_usd_thousand,g+a+e-new new_residual_usd_thousand FROM all_periods"""
CIRCLE_MARGIN_SQL="""WITH p AS (SELECT period,
SUM(CASE WHEN measure IN ('reserve_income','other_revenue') THEN amount_usd_thousand ELSE 0 END) r,
SUM(CASE WHEN measure IN ('distribution','other_costs') THEN amount_usd_thousand ELSE 0 END) c,
MAX(CASE WHEN measure='total_revenue' THEN amount_usd_thousand END) reported_r,
MAX(CASE WHEN measure='total_costs' THEN amount_usd_thousand END) reported_c,
MAX(CASE WHEN measure='adjusted_ebitda' THEN amount_usd_thousand END) e
FROM operations WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025') GROUP BY period)
SELECT period,r revenue_usd_thousand,r-c rldc_usd_thousand,100.0*(r-c)/r rldc_margin_pct,
100.0*e/(r-c) adjusted_ebitda_margin_pct,r-reported_r revenue_residual_usd_thousand,c-reported_c cost_residual_usd_thousand FROM p"""
CIRCLE_ATTRIBUTION_SQL="""WITH components AS (SELECT measure,
-MAX(CASE WHEN period='FY2024' THEN amount_usd_thousand END) p,
-MAX(CASE WHEN period='FY2025' THEN amount_usd_thousand END) c FROM expense_reconciliation
WHERE group_name='extra_adjustment' AND period IN ('FY2024','FY2025') GROUP BY measure),
delta AS (SELECT SUM(c-p) total FROM components)
SELECT measure,p prior_usd_thousand,c current_usd_thousand,c-p change_usd_thousand,
100.0*(c-p)/total contribution_to_definition_gap_change_pct FROM components CROSS JOIN delta"""


def coinbase_reference(data):
    facts={(r['period'],r['measure']):D(r['amount_usd_million']) for r in data['revenues']}
    delta=facts['FY2025','total_revenue']-facts['FY2024','total_revenue']
    attribution=[]
    for m in ('consumer','institutional','other_transaction','stablecoin','blockchain_rewards','interest_finance','other_subscription','corporate_interest'):
        p,c=facts['FY2024',m],facts['FY2025',m]
        attribution.append([m,float(p),float(c),float(c-p),float(100*(c-p)/delta)])
    transaction=[]
    for r in data['spot_volume']:
        if r['period']!='Q4FY2025':continue
        revenue=facts[r['period'],r['segment']]
        volume=D(r['volume_usd_billion'])
        transaction.append([r['segment'],float(revenue),float(volume),float(100*revenue/(volume*1000))])
    stablecoin=[]
    for r in data['usdc_economics']:
        if r['period']!='Q4FY2025':continue
        balance,revenue=D(r['average_usdc_usd_billion']),D(r['revenue_usd_million'])
        stablecoin.append([r['scope'],float(balance),float(revenue),float(100*revenue/(balance*1000)),float(400*revenue/(balance*1000))])
    return {'annual_revenue_bridge':attribution,'spot_revenue_proxy':transaction,'usdc_booked_ratio':stablecoin}


COINBASE_BRIDGE_SQL="""WITH components AS (SELECT measure,
MAX(CASE WHEN period='FY2024' THEN amount_usd_million END) p,
MAX(CASE WHEN period='FY2025' THEN amount_usd_million END) c FROM revenues
WHERE period IN ('FY2024','FY2025') AND measure IN ('consumer','institutional','other_transaction','stablecoin','blockchain_rewards','interest_finance','other_subscription','corporate_interest') GROUP BY measure),
totals AS (SELECT MAX(CASE WHEN period='FY2025' THEN amount_usd_million END)-MAX(CASE WHEN period='FY2024' THEN amount_usd_million END) delta
FROM revenues WHERE measure='total_revenue' AND period IN ('FY2024','FY2025'))
SELECT measure,p prior_usd_million,c current_usd_million,c-p change_usd_million,100.0*(c-p)/delta contribution_to_total_growth_pct FROM components CROSS JOIN totals"""
COINBASE_SPOT_SQL="""SELECT s.segment,r.amount_usd_million revenue_usd_million,s.volume_usd_billion spot_volume_usd_billion,
100.0*r.amount_usd_million/(1000*s.volume_usd_billion) apparent_revenue_to_spot_pct
FROM spot_volume s JOIN revenues r ON r.period=s.period AND r.measure=s.segment WHERE s.period='Q4FY2025'"""
COINBASE_USDC_SQL="""SELECT scope,average_usdc_usd_billion,revenue_usd_million,
100.0*revenue_usd_million/(1000*average_usdc_usd_billion) quarter_booked_ratio_pct,
400.0*revenue_usd_million/(1000*average_usdc_usd_billion) annualized_booked_ratio_pct FROM usdc_economics WHERE period='Q4FY2025'"""


def paypal_reference(data):
    quarters={r['period']:r for r in data['quarters']}
    activity=[]
    for p in ('Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025'):
        r=quarters[p]
        activity.append([p,r['active_accounts_million'],r['transactions_million'],float(D(r['transactions_million'])/D(r['active_accounts_million'])),r['reported_ttm_activity']])
    margin=[]
    for r in data['margin']:
        if r['period'] not in ('FY2024','FY2025','Q4FY2024','Q4FY2025'):continue
        revenue,expense,losses,interest=[D(r[k]) for k in ('net_revenue_usd_million','transaction_expense_usd_million','losses_usd_million','customer_interest_usd_million')]
        tm=revenue-expense-losses
        ex=tm-interest
        margin.append([r['period'],float(tm),float(ex),float(100*tm/revenue),float(100*ex/revenue),float(tm-D(r['reported_tm_usd_million'])),float(ex-D(r['reported_tm_ex_interest_usd_million']))])
    q=[quarters[p] for p in ('Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025')]
    transactions=sum((D(r['transactions_million']) for r in q),D(0))
    transaction_revenue=sum((D(r['transaction_revenue_usd_million']) for r in q),D(0))
    ovas=sum((D(r['ovas_usd_million']) for r in q),D(0))
    net=sum((D(r['net_revenue_usd_million']) for r in q),D(0))
    tpv=sum((D(r['tpv_usd_million']) for r in q),D(0))
    end=quarters['Q4FY2025']
    annual=[['FY2025',float(transactions),float(transactions/D(end['active_accounts_million'])),
             float(transactions/D(end['active_accounts_million'])-D(end['reported_ttm_activity'])),float(transaction_revenue),float(ovas),float(net),
             float(transaction_revenue+ovas-net),float(tpv),float(100*transaction_revenue/tpv)]]
    return {'quarter_activity':activity,'margin_reconciliation':margin,'annual_activity_bridge':annual}


PAYPAL_ACTIVITY_SQL="""SELECT period,active_accounts_million,transactions_million,
1.0*transactions_million/active_accounts_million quarter_transactions_per_active_account,reported_ttm_activity
FROM quarters WHERE period IN ('Q4FY2024','Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025')"""
PAYPAL_MARGIN_SQL="""WITH p AS (SELECT *,net_revenue_usd_million-transaction_expense_usd_million-losses_usd_million tm FROM margin
WHERE period IN ('FY2024','FY2025','Q4FY2024','Q4FY2025'))
SELECT period,tm transaction_margin_usd_million,tm-customer_interest_usd_million tm_ex_interest_usd_million,
100.0*tm/net_revenue_usd_million tm_margin_pct,100.0*(tm-customer_interest_usd_million)/net_revenue_usd_million tm_ex_interest_margin_pct,
tm-reported_tm_usd_million tm_residual_usd_million,tm-customer_interest_usd_million-reported_tm_ex_interest_usd_million ex_interest_residual_usd_million FROM p"""
PAYPAL_ANNUAL_SQL="""WITH annual AS (SELECT SUM(transactions_million) t,SUM(transaction_revenue_usd_million) r,
SUM(ovas_usd_million) o,SUM(net_revenue_usd_million) n,SUM(tpv_usd_million) v FROM quarters
WHERE period IN ('Q1FY2025','Q2FY2025','Q3FY2025','Q4FY2025'))
SELECT 'FY2025' period,t transactions_million,1.0*t/q.active_accounts_million recomputed_ttm_activity,
1.0*t/q.active_accounts_million-q.reported_ttm_activity rounded_activity_residual,r transaction_revenue_usd_million,
o ovas_usd_million,n net_revenue_usd_million,r+o-n revenue_residual_usd_million,v tpv_usd_million,100.0*r/v transaction_revenue_to_tpv_pct
FROM annual JOIN quarters q ON q.period='Q4FY2025'"""


def specifications():
    return {
      'a03':{'source':'circle-fy2025','split':'evaluation','calculate':circle_reference,
        'tables':{
          'expense_model':table({'period':TEXT,'gaap_expense_usd_thousand':K,'prior_adjusted_usd_thousand':K,'new_adjusted_usd_thousand':K,'additional_exclusions_usd_thousand':K,'prior_residual_usd_thousand':K,'new_residual_usd_thousand':K},['period'],[['a03:s01']]),
          'operating_margins':table({'period':TEXT,'revenue_usd_thousand':K,'rldc_usd_thousand':K,'rldc_margin_pct':P,'adjusted_ebitda_margin_pct':P,'revenue_residual_usd_thousand':K,'cost_residual_usd_thousand':K},['period'],[['a03:s02','a03:s03']]),
          'definition_attribution':table({'measure':TEXT,'prior_usd_thousand':K,'current_usd_thousand':K,'change_usd_thousand':K,'contribution_to_definition_gap_change_pct':P},['measure'],[['a03:s01']])},
        'sql':{'expense_model':CIRCLE_EXPENSE_SQL,'operating_margins':CIRCLE_MARGIN_SQL,'definition_attribution':CIRCLE_ATTRIBUTION_SQL},
        'starting':{'expense_model':CIRCLE_EXPENSE_SQL.replace('g+a+e new_adjusted','g+a new_adjusted')},
        'claims':{'new_definition_lower':claim('supported',['a03:s01'],'Annual FY2025 adjusted expenses are lower under the new definition than under the prior definition.'),
                  'ebitda_margin_uses_revenue':claim('contradicted',['a03:s03'],'The issuer defines adjusted EBITDA margin using total revenue as denominator.'),
                  'constant_balance_rate_effect_identified':claim('unresolved',['a03:s02','a03:s03'],'The supplied statements separately quantify the exact constant-balance rate effect on annual reserve income.')},
        'request':'Update the Circle workpaper through FY2025 under both disclosed adjusted-expense definitions. Preserve the seven disclosed annual/quarterly periods and reconstruct first-nine-month expense bridges for FY2024 and FY2025. Attribute the annual change in additional exclusions by component. Reconcile reserve and other income with distribution costs, then calculate the two issuer-defined margins for FY2024, FY2025 and both Q4 comparisons. Keep definition changes separate from an economic improvement claim.',
        'definitions':{'expense_model':'9MFY denotes the first nine months, annual less Q4. Adjustments retain source signs. Both reported-definition residuals compare recomputed amounts to reported amounts.',
          'definition_attribution':'Positive exclusions reduce expense. Changes are FY2025 less FY2024 and contributions divide by the change in the prior-minus-new definition gap.',
          'operating_margins':'Use exact USD thousand statement amounts. RLDC equals reserve plus other revenue less distribution and other costs. EBITDA margin uses the issuer denominator. No rounding to whole millions.'},
        'rationale':'A stablecoin issuer cost model can appear to improve solely because the adjusted definition changes. Updating both bases, deriving nine-month comparisons and reconciling two different margin denominators produces an actionable research artifact without inventing an interest-rate attribution.'},
      'b03':{'source':'coinbase-fy2025','split':'evaluation','calculate':coinbase_reference,
        'tables':{
          'annual_revenue_bridge':table({'measure':TEXT,'prior_usd_million':M,'current_usd_million':M,'change_usd_million':M,'contribution_to_total_growth_pct':P},['measure'],[['b03:s01']]),
          'spot_revenue_proxy':table({'segment':TEXT,'revenue_usd_million':M,'spot_volume_usd_billion':numeric('usd_billion'),'apparent_revenue_to_spot_pct':P},['segment'],[['b03:s01','b03:s02']]),
          'usdc_booked_ratio':table({'scope':TEXT,'average_usdc_usd_billion':numeric('usd_billion'),'revenue_usd_million':M,'quarter_booked_ratio_pct':P,'annualized_booked_ratio_pct':P},['scope'],[['b03:s03']])},
        'sql':{'annual_revenue_bridge':COINBASE_BRIDGE_SQL,'spot_revenue_proxy':COINBASE_SPOT_SQL,'usdc_booked_ratio':COINBASE_USDC_SQL},
        'starting':{'usdc_booked_ratio':COINBASE_USDC_SQL.replace('400.0*revenue','100.0*revenue')},
        'claims':{'stablecoin_majority_growth':claim('supported',['b03:s01'],'Stablecoin revenue contributed more than half the FY2024-to-FY2025 increase in total revenue.'),
          'institutional_spot_commission_identified':claim('unresolved',['b03:s02'],'The supplied revenue and spot-volume disclosures identify the institutional spot commission rate.'),
          'custodial_missing_means_zero':claim('contradicted',['b03:s01'],'No separate custodial fee line in FY2025 means custodial revenue was zero.')},
        'request':'Audit the Coinbase revenue-yield workpaper through FY2025. Preserve the annual revenue contribution bridge using recast categories and corporate interest. Repair quarterly versus annualized USDC booked-revenue ratios separately on and off platform. Show the consumer and institutional Q4 revenue-to-spot-volume proxies, but resolve whether those proxies identify commission rates. Do not mix total derivative notional with spot volume or treat a condensed disclosure as zero.',
        'definitions':{'annual_revenue_bridge':'Use eight mutually exclusive components. Contribution is the component change divided by reported total revenue change, with small source-rounding residuals allowed in interpretation.',
          'spot_revenue_proxy':'Revenue is USD million, spot volume USD billion. Ratios are percent and are explicitly proxies, with no assertion of identical numerator and denominator scope.',
          'usdc_booked_ratio':'Use the rounded Q4 USDC table amounts as supplied. Quarterly ratio is revenue/average balance, annualized ratio is four times that ratio, not an effective compounded yield or payments volume.'},
        'rationale':'A research project can perform valid revenue arithmetic while mislabeling a derivatives-inclusive numerator as a spot fee. A second scope problem arises when USDC revenue is compared with balances using inconsistent units or periods. Preserve useful arithmetic and mark the non-identifiable fee inference unresolved.'},
      'b05':{'source':'paypal-fy2025','split':'evaluation','calculate':paypal_reference,
        'tables':{
          'quarter_activity':table({'period':TEXT,'active_accounts_million':numeric('million_accounts'),'transactions_million':numeric('million_transactions'),'quarter_transactions_per_active_account':numeric('transactions_per_account'),'reported_ttm_activity':numeric('transactions_per_account')},['period'],[['b05:s01','b05:s02']]),
          'margin_reconciliation':table({'period':TEXT,'transaction_margin_usd_million':M,'tm_ex_interest_usd_million':M,'tm_margin_pct':P,'tm_ex_interest_margin_pct':P,'tm_residual_usd_million':M,'ex_interest_residual_usd_million':M},['period'],[['b05:s03']]),
          'annual_activity_bridge':table({'period':TEXT,'transactions_million':numeric('million_transactions'),'recomputed_ttm_activity':numeric('transactions_per_account'),'rounded_activity_residual':numeric('transactions_per_account'),'transaction_revenue_usd_million':M,'ovas_usd_million':M,'net_revenue_usd_million':M,'revenue_residual_usd_million':M,'tpv_usd_million':M,'transaction_revenue_to_tpv_pct':P},['period'],[['b05:s01','b05:s02']])},
        'sql':{'quarter_activity':PAYPAL_ACTIVITY_SQL,'margin_reconciliation':PAYPAL_MARGIN_SQL,'annual_activity_bridge':PAYPAL_ANNUAL_SQL},
        'starting':{'annual_activity_bridge':PAYPAL_ANNUAL_SQL.replace('1.0*t/q.active_accounts_million recomputed','1.0*q.transactions_million/q.active_accounts_million recomputed')},
        'claims':{'quarter_ratio_equals_ttm':claim('contradicted',['b05:s01','b05:s02'],'Dividing Q4FY2025 transactions by December active accounts reproduces the issuer trailing-twelve-month activity measure.'),
          'unique_people_identifiable':claim('unresolved',['b05:s02'],'The supplied account counts identify the exact number of distinct people using PayPal.'),
          'annual_ex_interest_margin_dollars_increased':claim('supported',['b05:s03'],'Annual transaction margin dollars excluding customer interest increased from FY2024 to FY2025.')},
        'request':'Repair the PayPal engagement and margin workpaper through FY2025. Keep the five valid quarter rows, distinguish quarterly from trailing-year engagement, and reconstruct the annual activity and revenue bridge from four quarters. Reconcile transaction margin and its customer-interest exclusion for both annual and Q4 comparisons. Report rounding residuals instead of forcing them to zero, and distinguish payment value, recognized revenue and account activity.',
        'definitions':{'quarter_activity':'Quarter flows are divided by active accounts at period end. Keep the reported trailing-year ratio alongside the distinct quarterly calculation.',
          'margin_reconciliation':'Margin dollars equal net revenue less transaction expense and transaction/credit losses. Ex-interest subtracts customer-balance interest. Percent margins use net revenue.',
          'annual_activity_bridge':'FY2025 sums only its four quarters and uses Q4 end accounts for trailing-year activity. Activity residual is recomputed less reported rounded ratio. Revenue residual is transaction plus OVAS less net revenue.'},
        'rationale':'Quarterly transactions are often paired with a trailing-year account metric. Fixing that period mismatch must preserve the valid quarter calculations and margin reconciliation. The revenue bridge and interest exclusion prevent payment value, pricing and financial margin from being treated as interchangeable.'}}


def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for row in rows:
            for field,value in row.items():
                if isinstance(value,(int,float)) and field!='reported_ttm_activity':row[field]=value*2
    yield 'scaled_amounts_preserve_ratios',scaled
    changed=copy.deepcopy(data)
    if key=='a03':
        for row in changed['expense_reconciliation']:
            if row['period'] in ('FY2025','Q4FY2025'):
                if row['measure'] in ('gaap','prior_definition'):row['amount_usd_thousand']+=1000
                if row['measure']=='payroll_tax':row['amount_usd_thousand']-=1000
        yield 'excluded_payroll_increase_new_expense_unchanged',changed
    elif key=='b03':
        for row in changed['usdc_economics']:
            if row['scope']=='on_platform':row['average_usdc_usd_billion']+=1
            if row['scope']=='off_platform':row['average_usdc_usd_billion']-=1
        yield 'platform_balance_mix_changes_scoped_ratios',changed
    else:
        for row in changed['margin']:
            if row['period'] in ('FY2025','Q4FY2025'):
                row['customer_interest_usd_million']+=100
                row['net_revenue_usd_million']+=100
                row['reported_tm_usd_million']+=100
        for row in changed['quarters']:
            if row['period']=='Q4FY2025':
                row['ovas_usd_million']+=100
                row['net_revenue_usd_million']+=100
        yield 'customer_interest_changes_tm_not_ex_interest',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        additions=copy.deepcopy(rows)
        for row in additions:row['period']=row['period'].replace('2025','2026').replace('2024','2027')
        later[name]+=additions
    yield 'irrelevant_later_disclosures',later
