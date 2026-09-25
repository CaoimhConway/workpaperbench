"""Independent references for cash-generation and cumulative financial updates."""
import copy
from decimal import Decimal
from build_workflow_tasks import INTEGER, TEXT, numeric, table
from workflow_development_cases import claim

D=lambda v:Decimal(str(v))
M=numeric('usd_million',0.001)
P=numeric('percent')


def amazon(data):
    facts={(r['fiscal_year'],r['months'],r['measure']):D(r['amount_usd_million']) for r in data['cashflows']}
    generation,movement,noncash=[],[],[]
    for year in (2024,2025):
        for months in (3,9,12):
            def f(m):return facts[year,12,m]-facts[year,3,m] if months==9 else facts[year,months,m]
            ocf=f('Net cash provided by (used in) operating activities')
            purchase=-f('Purchases of property and equipment')
            proceeds=f('Proceeds from property and equipment sales and incentives')
            leases=-f('Principal repayments of finance leases')
            obligations=-f('Principal repayments of financing obligations')
            fcf=ocf-purchase+proceeds
            generation.append([year,months,float(ocf),float(purchase),float(proceeds),float(purchase-proceeds),float(fcf),float(fcf-leases),float(fcf-leases-obligations)])
            investing=f('Net cash provided by (used in) investing activities')
            financing=f('Net cash provided by (used in) financing activities')
            fx=f('Foreign currency effect on cash, cash equivalents, and restricted cash')
            net=f('Net increase (decrease) in cash, cash equivalents, and restricted cash')
            movement.append([year,months,float(investing),float(financing),float(fx),float(net),float(ocf+investing+financing+fx-net)])
            noncash.append([year,months,float(f('Assets acquired under operating leases')),
              float(f('Property and equipment acquired under finance leases, net of remeasurements and modifications')),
              float(f('Increase (decrease) in property and equipment acquired but not yet paid'))])
    return {'cash_generation':generation,'cash_movement':movement,'noncash_capital':noncash}


AMAZON_PERIODS="""WITH p AS (SELECT fiscal_year,months,
MAX(CASE WHEN measure='Net cash provided by (used in) operating activities' THEN amount_usd_million END) ocf,
-MAX(CASE WHEN measure='Purchases of property and equipment' THEN amount_usd_million END) purchase,
MAX(CASE WHEN measure='Proceeds from property and equipment sales and incentives' THEN amount_usd_million END) proceeds,
-MAX(CASE WHEN measure='Principal repayments of finance leases' THEN amount_usd_million END) lease,
-MAX(CASE WHEN measure='Principal repayments of financing obligations' THEN amount_usd_million END) obligation,
MAX(CASE WHEN measure='Net cash provided by (used in) investing activities' THEN amount_usd_million END) investing,
MAX(CASE WHEN measure='Net cash provided by (used in) financing activities' THEN amount_usd_million END) financing,
MAX(CASE WHEN measure='Foreign currency effect on cash, cash equivalents, and restricted cash' THEN amount_usd_million END) fx,
MAX(CASE WHEN measure='Net increase (decrease) in cash, cash equivalents, and restricted cash' THEN amount_usd_million END) net,
MAX(CASE WHEN measure='Assets acquired under operating leases' THEN amount_usd_million END) operating_assets,
MAX(CASE WHEN measure='Property and equipment acquired under finance leases, net of remeasurements and modifications' THEN amount_usd_million END) finance_assets,
MAX(CASE WHEN measure='Increase (decrease) in property and equipment acquired but not yet paid' THEN amount_usd_million END) unpaid
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.ocf-q.ocf,a.purchase-q.purchase,a.proceeds-q.proceeds,a.lease-q.lease,a.obligation-q.obligation,
a.investing-q.investing,a.financing-q.financing,a.fx-q.fx,a.net-q.net,a.operating_assets-q.operating_assets,a.finance_assets-q.finance_assets,a.unpaid-q.unpaid
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=12 AND q.months=3) """
AMAZON_GENERATION=AMAZON_PERIODS+"""SELECT fiscal_year,months,ocf operating_cash_usd_million,purchase gross_property_spending_usd_million,
proceeds sales_and_incentives_usd_million,purchase-proceeds net_property_spending_usd_million,ocf-purchase+proceeds issuer_fcf_usd_million,
ocf-purchase+proceeds-lease after_finance_lease_principal_usd_million,ocf-purchase+proceeds-lease-obligation after_all_capital_principal_usd_million FROM periods"""
AMAZON_MOVEMENT=AMAZON_PERIODS+"""SELECT fiscal_year,months,investing investing_cash_usd_million,financing financing_cash_usd_million,
fx currency_effect_usd_million,net cash_change_usd_million,ocf+investing+financing+fx-net residual_usd_million FROM periods"""
AMAZON_NONCASH=AMAZON_PERIODS+"""SELECT fiscal_year,months,operating_assets operating_lease_assets_usd_million,
finance_assets finance_lease_property_usd_million,unpaid unpaid_property_change_usd_million FROM periods"""


def costco(data):
    facts={(r['fiscal_year'],r['weeks']):r for r in data['income']}
    model,attribution=[],[]
    derived={}
    fields=['net_sales_usd_million','membership_usd_million','revenue_usd_million','merchandise_cost_usd_million','sga_usd_million','operating_income_usd_million']
    for year in (2024,2025):
        for weeks in (16,36,52):
            r={k:D(facts[year,52][k])-D(facts[year,16][k]) if weeks==36 else D(facts[year,weeks][k]) for k in fields}
            gross=r['net_sales_usd_million']-r['merchandise_cost_usd_million']
            op=gross+r['membership_usd_million']-r['sga_usd_million']
            model.append([year,weeks,float(r['net_sales_usd_million']),float(r['membership_usd_million']),float(gross),float(100*gross/r['net_sales_usd_million']),float(op),float(op-r['operating_income_usd_million'])])
            derived[year,weeks]=(gross,r['membership_usd_million'],-r['sga_usd_million'],op)
    for weeks in (16,36,52):
        p,c=derived[2024,weeks],derived[2025,weeks]
        delta=c[3]-p[3]
        for i,name in enumerate(('merchandise_gross_profit','membership_fees','sga')):
            attribution.append([weeks,name,float(p[i]),float(c[i]),float(c[i]-p[i]),float(100*(c[i]-p[i])/delta)])
    balances={r['economic_date']:D(r['amount_usd_million']) for r in data['deferred_membership']}
    before,after=balances['2024-09-01'],balances['2025-08-31']
    earned=D(facts[2025,52]['membership_usd_million'])
    return {'income_model':model,'operating_growth_bridge':attribution,
      'membership_accrual_bridge':[['FY2025',float(earned),float(before),float(after),float(after-before),float(earned+after-before)]]}


COSTCO_PERIODS="""WITH periods AS (SELECT * FROM income WHERE fiscal_year IN (2024,2025) UNION ALL
SELECT a.fiscal_year,36,a.net_sales_usd_million-q.net_sales_usd_million,a.membership_usd_million-q.membership_usd_million,
a.revenue_usd_million-q.revenue_usd_million,a.merchandise_cost_usd_million-q.merchandise_cost_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million
FROM income a JOIN income q ON a.fiscal_year=q.fiscal_year AND a.weeks=52 AND q.weeks=16 WHERE a.fiscal_year IN (2024,2025)) """
COSTCO_MODEL=COSTCO_PERIODS+"""SELECT fiscal_year,weeks,net_sales_usd_million,membership_usd_million,
net_sales_usd_million-merchandise_cost_usd_million merchandise_gross_profit_usd_million,
100.0*(net_sales_usd_million-merchandise_cost_usd_million)/net_sales_usd_million merchandise_gross_margin_pct,
net_sales_usd_million-merchandise_cost_usd_million+membership_usd_million-sga_usd_million operating_income_usd_million,
net_sales_usd_million-merchandise_cost_usd_million+membership_usd_million-sga_usd_million-operating_income_usd_million residual_usd_million FROM periods"""
COSTCO_ATTRIBUTION=COSTCO_PERIODS+""",components AS (
SELECT fiscal_year,weeks,'merchandise_gross_profit' measure,net_sales_usd_million-merchandise_cost_usd_million amount FROM periods
UNION ALL SELECT fiscal_year,weeks,'membership_fees',membership_usd_million FROM periods
UNION ALL SELECT fiscal_year,weeks,'sga',-sga_usd_million FROM periods)
SELECT c.weeks,c.measure,p.amount prior_usd_million,c.amount current_usd_million,c.amount-p.amount change_usd_million,
100.0*(c.amount-p.amount)/(ct.operating_income_usd_million-pt.operating_income_usd_million) contribution_to_operating_growth_pct
FROM components c JOIN components p ON c.fiscal_year=2025 AND p.fiscal_year=2024 AND c.weeks=p.weeks AND c.measure=p.measure
JOIN periods ct ON ct.fiscal_year=2025 AND ct.weeks=c.weeks JOIN periods pt ON pt.fiscal_year=2024 AND pt.weeks=c.weeks"""
COSTCO_ACCRUAL="""SELECT 'FY2025' period,i.membership_usd_million earned_fees_usd_million,p.amount_usd_million opening_deferred_usd_million,
c.amount_usd_million closing_deferred_usd_million,c.amount_usd_million-p.amount_usd_million deferred_change_usd_million,
i.membership_usd_million+c.amount_usd_million-p.amount_usd_million mechanical_accrual_bridge_usd_million
FROM income i JOIN deferred_membership p ON p.economic_date='2024-09-01' JOIN deferred_membership c ON c.economic_date='2025-08-31'
WHERE i.fiscal_year=2025 AND i.weeks=52"""


def walmart(data):
    income={(r['fiscal_year'],r['months']):r for r in data['income']}
    adjustments={(r['fiscal_year'],r['months']):r for r in data['adjustments']}
    model,bridge=[],[]
    for year in (2025,2026):
        for months in (3,6,9):
            def f(rows,key):return D(rows[year,9][key])-D(rows[year,3][key]) if months==6 else D(rows[year,months][key])
            revenue=f(income,'revenue_usd_million')
            op=revenue-f(income,'cost_sales_usd_million')-f(income,'sga_usd_million')
            a=[f(adjustments,k) for k in ('phonepe_sbc_usd_million','legal_usd_million','reorganization_usd_million')]
            adjusted=op+sum(a,D(0))
            fx=f(adjustments,'adjusted_currency_usd_million')
            model.append([year,months,float(revenue),float(op),float(adjusted),float(adjusted+fx),float(100*op/revenue),float(100*adjusted/revenue)])
            bridge.append([year,months,*map(float,a),float(fx),float(op-f(income,'operating_income_usd_million')),
              float(adjusted-f(adjustments,'reported_adjusted_usd_million')),float(adjusted+fx-f(adjustments,'reported_adjusted_cc_usd_million'))])
    cash=[]
    for r in data['cashflows']:
        if r['fiscal_year'] not in (2025,2026) or r['months']!=9:continue
        operating,spending=D(r['operating_cash_usd_million']),D(r['capital_spending_usd_million'])
        cash.append([r['fiscal_year'],9,float(operating),float(spending),float(operating-spending),float(operating-spending-D(r['reported_fcf_usd_million']))])
    return {'income_model':model,'adjustment_bridge':bridge,'year_to_date_cash':cash}


WALMART_PERIODS="""WITH p AS (SELECT i.*,a.phonepe_sbc_usd_million,a.legal_usd_million,a.reorganization_usd_million,a.reported_adjusted_usd_million,
a.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million FROM income i JOIN adjustments a USING(fiscal_year,months) WHERE fiscal_year IN (2025,2026)),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,6,a.revenue_usd_million-q.revenue_usd_million,a.cost_sales_usd_million-q.cost_sales_usd_million,
a.sga_usd_million-q.sga_usd_million,a.operating_income_usd_million-q.operating_income_usd_million,
a.phonepe_sbc_usd_million-q.phonepe_sbc_usd_million,a.legal_usd_million-q.legal_usd_million,a.reorganization_usd_million-q.reorganization_usd_million,
a.reported_adjusted_usd_million-q.reported_adjusted_usd_million,a.adjusted_currency_usd_million-q.adjusted_currency_usd_million,a.reported_adjusted_cc_usd_million-q.reported_adjusted_cc_usd_million
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year AND a.months=9 AND q.months=3),
computed AS (SELECT *,revenue_usd_million-cost_sales_usd_million-sga_usd_million op,
revenue_usd_million-cost_sales_usd_million-sga_usd_million+phonepe_sbc_usd_million+legal_usd_million+reorganization_usd_million adjusted FROM periods) """
WALMART_MODEL=WALMART_PERIODS+"""SELECT fiscal_year,months,revenue_usd_million,op gaap_operating_income_usd_million,
adjusted adjusted_operating_income_usd_million,adjusted+adjusted_currency_usd_million adjusted_cc_operating_income_usd_million,
100.0*op/revenue_usd_million gaap_margin_pct,100.0*adjusted/revenue_usd_million adjusted_margin_pct FROM computed"""
WALMART_BRIDGE=WALMART_PERIODS+"""SELECT fiscal_year,months,phonepe_sbc_usd_million,legal_usd_million,reorganization_usd_million,
adjusted_currency_usd_million,op-operating_income_usd_million gaap_residual_usd_million,
adjusted-reported_adjusted_usd_million adjusted_residual_usd_million,
adjusted+adjusted_currency_usd_million-reported_adjusted_cc_usd_million cc_residual_usd_million FROM computed"""
WALMART_CASH="""SELECT fiscal_year,months,operating_cash_usd_million,capital_spending_usd_million,
operating_cash_usd_million-capital_spending_usd_million free_cash_flow_usd_million,
operating_cash_usd_million-capital_spending_usd_million-reported_fcf_usd_million residual_usd_million FROM cashflows WHERE fiscal_year IN (2025,2026) AND months=9"""


def specifications():
    period={'fiscal_year':INTEGER,'months':INTEGER}
    return {
      'a04':{'source':'amazon-fy2025','split':'evaluation','calculate':amazon,
        'tables':{'cash_generation':table(dict(period,operating_cash_usd_million=M,gross_property_spending_usd_million=M,sales_and_incentives_usd_million=M,net_property_spending_usd_million=M,issuer_fcf_usd_million=M,after_finance_lease_principal_usd_million=M,after_all_capital_principal_usd_million=M),['fiscal_year','months'],[['a04:s01','a04:s02']]),
          'cash_movement':table(dict(period,investing_cash_usd_million=M,financing_cash_usd_million=M,currency_effect_usd_million=M,cash_change_usd_million=M,residual_usd_million=M),['fiscal_year','months'],[['a04:s01','a04:s03']]),
          'noncash_capital':table(dict(period,operating_lease_assets_usd_million=M,finance_lease_property_usd_million=M,unpaid_property_change_usd_million=M),['fiscal_year','months'],[['a04:s01']])},
        'sql':{'cash_generation':AMAZON_GENERATION,'cash_movement':AMAZON_MOVEMENT,'noncash_capital':AMAZON_NONCASH},
        'starting':{'cash_generation':AMAZON_GENERATION.replace('ocf-purchase+proceeds issuer_fcf','ocf-purchase issuer_fcf')},
        'claims':{'annual_fcf_increased':claim('contradicted',['a04:s01','a04:s02'],'Issuer annual free cash flow increased from FY2024 to FY2025.'),
          'unpaid_property_is_cash_outflow':claim('contradicted',['a04:s01'],'The increase in acquired-but-unpaid property is an additional same-period cash outflow.'),
          'exact_ai_cash_spending_identified':claim('unresolved',['a04:s01','a04:s02'],'The supplied statement separately quantifies the exact cash property spending attributable to artificial intelligence.')},
        'request':'Update Amazon cash-generation and capital-funding analysis through FY2025. Preserve FY2024 and both Q4 periods, reconstruct nine-month flows, and reconcile total cash movement. Apply the issuer net-property-spending definition before showing separate analyst cash-flow measures after finance-lease and financing-obligation principal. Keep supplemental noncash acquisition observations outside cash spending.',
        'definitions':{'cash_generation':'months=3 is Q4, 9 first nine months, 12 full year. Gross spending and principal repayment deductions are positive outflow amounts. The two further principal deductions are analyst cash measures, not issuer FCF.',
          'cash_movement':'Cash change includes currency effects and the source cash/restricted-cash scope. Residual is operating plus investing plus financing plus currency effects less reported period change.',
          'noncash_capital':'Three separate supplemental observations, retaining source signs. They are not summed into cash expenditures.'},
        'rationale':'Cash capex, net incentives, finance-lease principal and acquired-but-unpaid assets answer different funding questions. An update must preserve their statement scope and cumulative periods rather than inflate cash spending or rename an analyst measure as issuer free cash flow.'},
      'a05':{'source':'costco-fy2025','split':'evaluation','calculate':costco,
        'tables':{'income_model':table({'fiscal_year':INTEGER,'weeks':INTEGER,'net_sales_usd_million':M,'membership_usd_million':M,'merchandise_gross_profit_usd_million':M,'merchandise_gross_margin_pct':P,'operating_income_usd_million':M,'residual_usd_million':M},['fiscal_year','weeks'],[['a05:s01']]),
          'operating_growth_bridge':table({'weeks':INTEGER,'measure':TEXT,'prior_usd_million':M,'current_usd_million':M,'change_usd_million':M,'contribution_to_operating_growth_pct':P},['weeks','measure'],[['a05:s01']]),
          'membership_accrual_bridge':table({'period':TEXT,'earned_fees_usd_million':M,'opening_deferred_usd_million':M,'closing_deferred_usd_million':M,'deferred_change_usd_million':M,'mechanical_accrual_bridge_usd_million':M},['period'],[['a05:s01','a05:s02']])},
        'sql':{'income_model':COSTCO_MODEL,'operating_growth_bridge':COSTCO_ATTRIBUTION,'membership_accrual_bridge':COSTCO_ACCRUAL},
        'starting':{'income_model':COSTCO_MODEL.replace('net_sales_usd_million-merchandise_cost_usd_million merchandise_gross_profit','revenue_usd_million-merchandise_cost_usd_million merchandise_gross_profit')},
        'claims':{'quarter_is_one_fourth_of_year':claim('contradicted',['a05:s01'],'The supplied Q4 periods each contain one quarter of the full-year number of weeks.'),
          'membership_growth_contributes_to_operating_growth':claim('supported',['a05:s01'],'Higher FY2025 earned membership fees contribute positively to the operating-income increase.'),
          'exact_fee_cash_receipts_identified':claim('unresolved',['a05:s02'],'Earned fees plus the deferred balance change uniquely identifies exact cash membership collections.')},
        'request':'Update Costco FY2025 operating and membership workpapers. Preserve both 16-week quarters and 52-week years, reconstruct first 36 weeks, and separate merchandise gross profit from membership fees. Attribute operating-income growth to merchandise margin dollars, earned fees and SG&A. Add a clearly labeled mechanical membership accrual bridge while deciding whether it identifies actual cash collections.',
        'definitions':{'income_model':'Output 16, 36 and 52 weeks for both years. Merchandise margin excludes earned membership fees from its numerator and uses net sales as denominator.',
          'operating_growth_bridge':'Changes are FY2025 less FY2024 for each matched duration. SG&A is a signed negative contribution. Denominator is that duration operating-income change.',
          'membership_accrual_bridge':'The mechanical bridge is FY2025 earned fees plus closing less opening deferred fees. It is not labeled observed collections.'},
        'rationale':'A retail model can double-count membership economics in merchandise margin and misread a 16-week quarter as 13 weeks. Updating matched durations and explaining an accrual bridge leaves useful work even when actual cash collections and price/renewal effects remain unidentified.'},
      'a06':{'source':'walmart-q3fy2026','split':'evaluation','calculate':walmart,
        'tables':{'income_model':table(dict(period,revenue_usd_million=M,gaap_operating_income_usd_million=M,adjusted_operating_income_usd_million=M,adjusted_cc_operating_income_usd_million=M,gaap_margin_pct=P,adjusted_margin_pct=P),['fiscal_year','months'],[['a06:s01','a06:s02']]),
          'adjustment_bridge':table(dict(period,phonepe_sbc_usd_million=M,legal_usd_million=M,reorganization_usd_million=M,adjusted_currency_usd_million=M,gaap_residual_usd_million=M,adjusted_residual_usd_million=M,cc_residual_usd_million=M),['fiscal_year','months'],[['a06:s01','a06:s02']]),
          'year_to_date_cash':table(dict(period,operating_cash_usd_million=M,capital_spending_usd_million=M,free_cash_flow_usd_million=M,residual_usd_million=M),['fiscal_year','months'],[['a06:s03']])},
        'sql':{'income_model':WALMART_MODEL,'adjustment_bridge':WALMART_BRIDGE,'year_to_date_cash':WALMART_CASH},
        'starting':{'income_model':WALMART_MODEL.replace('adjusted+adjusted_currency_usd_million adjusted_cc','op+adjusted_currency_usd_million adjusted_cc')},
        'claims':{'q3_gaap_and_adjusted_diverge':claim('supported',['a06:s01','a06:s02'],'Current Q3 GAAP operating income declined while adjusted operating income increased versus the prior Q3.'),
          'headline_cash_is_q3':claim('contradicted',['a06:s03'],'The supplied USD 27.5 billion operating cash headline covers only Q3.'),
          'exact_q3_operating_cash_identified':claim('unresolved',['a06:s03'],'The supplied cash disclosures identify exact Q3 operating cash flow.')},
        'request':'Update Walmart through Q3FY2026. Preserve both Q3 and nine-month comparisons and reconstruct first-six-month earnings outputs. Reconcile signed legal, PhonePe and reorganization adjustments before applying the adjusted currency bridge. Keep year-to-date cash flow in its nine-month scope and assess whether quarter cash flow can be reconstructed.',
        'definitions':{'income_model':'months=3 denotes Q3, 6 first six months, 9 first nine months. Fiscal years are 2026 for economic periods in 2025 and 2025 for periods in 2024. Earnings margins use total revenue.',
          'adjustment_bridge':'First-six-month adjustments are nine months less Q3. Adjusted currency is the reported adjusted-income currency bridge, not the GAAP currency bridge. Residuals compare each recomputed basis with its matching reported basis.',
          'year_to_date_cash':'Only nine-month rows are requested and supported. FCF is operating cash less positive capital spending.'},
        'rationale':'A noncash IPO charge, a signed quarter legal benefit and different GAAP/adjusted currency bridges can reverse an earnings narrative. An update must preserve cumulative scope and fiscal naming, while incomplete cash periods require a supported non-answer.'}}


def controls(key,data):
    scaled=copy.deepcopy(data)
    for rows in scaled.values():
        for row in rows:
            for field,value in row.items():
                if isinstance(value,(int,float)) and field not in ('fiscal_year','months','weeks'):row[field]=value*2
    yield 'scaled_amounts_preserve_ratios',scaled
    changed=copy.deepcopy(data)
    if key=='a04':
        for r in changed['cashflows']:
            if r['fiscal_year']==2025:
                if r['measure']=='Purchases of property and equipment':r['amount_usd_million']-=100
                if r['measure']=='Proceeds from property and equipment sales and incentives':r['amount_usd_million']+=100
        yield 'gross_spending_and_incentives_net_unchanged',changed
    elif key=='a05':
        for r in changed['income']:
            if r['fiscal_year']==2025:
                for f in ('membership_usd_million','revenue_usd_million','operating_income_usd_million'):r[f]+=10
        yield 'earned_membership_changes_not_merchandise_margin',changed
    else:
        for r in changed['adjustments']:
            if r['fiscal_year']==2026:
                r['phonepe_sbc_usd_million']+=10
        for r in changed['income']:
            if r['fiscal_year']==2026:
                r['sga_usd_million']+=10
                r['operating_income_usd_million']-=10
        yield 'excluded_phonepe_charge_changes_gaap_not_adjusted',changed
    later=copy.deepcopy(data)
    for name,rows in list(later.items()):
        if name=='deferred_membership':continue
        additions=copy.deepcopy(rows)
        for r in additions:r['fiscal_year']+=3
        later[name]+=additions
    yield 'irrelevant_later_periods',later
