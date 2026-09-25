"""Build the three source-backed development workflow prototypes offline."""
import argparse
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workpaperbench.catalog import content_hash, load, tree_hash

D = lambda value: Decimal(str(value))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def observations(database):
    connection = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    result = {name: [dict(row) for row in connection.execute('SELECT * FROM [' + name + ']')]
              for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    connection.close()
    return result


def numeric(unit, tolerance=0.000001):
    return {'type': 'real', 'unit': unit, 'tolerance': tolerance}


def table(columns, keys, evidence):
    return {'columns': columns, 'keys': keys, 'duplicates': 'Keys must be unique',
            'row_order': 'ignored', 'evidence': evidence}


TEXT = {'type': 'text', 'unit': 'label'}
INTEGER = {'type': 'integer', 'unit': 'count'}


def microsoft(data):
    facts = {(row['period_end'], row['months'], row['measure']): D(row['amount']) for row in data['financials']}
    quarters, reconciliation = [], []
    for year in (2023, 2024):
        end = str(year) + '-12-31'
        revenue2, income2 = facts[end, 3, 'Total revenue'], facts[end, 3, 'Operating income']
        revenue1, income1 = facts[end, 6, 'Total revenue'] - revenue2, facts[end, 6, 'Operating income'] - income2
        for quarter, revenue, income in ((1, revenue1, income1), (2, revenue2, income2)):
            quarters.append([year + 1, quarter, float(revenue), float(income), float(100 * income / revenue)])
        reconciliation.append([year + 1, float(revenue1 + revenue2 - facts[end, 6, 'Total revenue']),
                               float(income1 + income2 - facts[end, 6, 'Operating income']),
                               float(10000 * (income2 / revenue2 - income1 / revenue1))])
    actual = next(D(row['constant_currency_percent']) for row in data['growth'] if row['business'] == 'Azure and other cloud services')
    earlier = next(row for row in data['guidance'] if row['issue_date'] == '2024-10-30')
    low, high = D(earlier['low']), D(earlier['high'])
    return {'quarter_model': quarters, 'quarter_reconciliation': reconciliation,
            'guidance_bridge': [['Azure and other cloud services', float(actual), float(low), float(high),
                                 float(actual - (low + high) / 2)]]}


def brale(data):
    from datetime import date
    by_date = {}
    for row in data['reserve_reports']:
        if row['report_date'] in by_date and row != by_date[row['report_date']]:
            raise ValueError('conflicting_report_identity')
        by_date[row['report_date']] = row
    coverage, lag = [], []
    for observed in ('2025-05-31', '2025-06-30'):
        row = by_date[observed]
        reserves = D(row['cash_equivalents_usd']) + D(row['us_government_debt_usd'])
        coverage.append([observed, float(reserves), row['issued_sbc'], float(100 * reserves / D(row['issued_sbc'])),
                         float(reserves - D(row['reported_reserve_fv_usd']))])
        lag.append([observed, row['report_signed_date'], (date.fromisoformat(row['report_signed_date']) - date.fromisoformat(observed)).days])
    prior, current = (by_date[name] for name in ('2025-05-31', '2025-06-30'))
    cash = D(current['cash_equivalents_usd']) - D(prior['cash_equivalents_usd'])
    debt = D(current['us_government_debt_usd']) - D(prior['us_government_debt_usd'])
    return {'reserve_coverage': coverage, 'signature_lag': lag,
            'reserve_bridge': [['2025-05-31', '2025-06-30', float(cash), float(debt), float(cash + debt),
                                current['issued_sbc'] - prior['issued_sbc'], (coverage[1][3] - coverage[0][3]) * 100]]}


def block(data):
    rev = {(row['period_end'], row['category']): D(row['amount']) for row in data['revenues'] if row['months'] == 12}
    cost = {(row['period_end'], row['category']): D(row['amount']) for row in data['costs'] if row['months'] == 12}
    prior, current = '2023-12-31', '2024-12-31'
    total_delta = rev[current, 'Total net revenue'] - rev[prior, 'Total net revenue']
    revenues, profits = [], []
    for name, label in (('Transaction-based', 'transaction'), ('Subscription and services-based', 'subscription'),
                        ('Hardware', 'hardware'), ('Bitcoin', 'bitcoin')):
        before, after = rev[prior, name + ' revenue'], rev[current, name + ' revenue']
        prior_share = 100 * before / rev[prior, 'Total net revenue']
        current_share = 100 * after / rev[current, 'Total net revenue']
        revenues.append([label, float(before), float(after), float(after - before), float(100 * (after - before) / total_delta),
                         float(prior_share), float(current_share), float(current_share - prior_share)])
        profit0, profit1 = before - cost[prior, name + ' costs'], after - cost[current, name + ' costs']
        profits.append([label, float(profit0), float(profit1), float(profit1 - profit0)])
    amort = 'Amortization of acquired technology assets'
    profits.append(['acquired_technology_amortization', float(-cost[prior, amort]), float(-cost[current, amort]),
                    float(cost[prior, amort] - cost[current, amort])])
    profit_total_delta = (rev[current, 'Total net revenue'] - cost[current, 'Total cost of revenue']) - (rev[prior, 'Total net revenue'] - cost[prior, 'Total cost of revenue'])
    bitcoin0 = rev[prior, 'Bitcoin revenue'] - cost[prior, 'Bitcoin costs']
    bitcoin1 = rev[current, 'Bitcoin revenue'] - cost[current, 'Bitcoin costs']
    return {'revenue_bridge': revenues, 'profit_bridge': profits,
            'reconciliation': [[float(total_delta), float(profit_total_delta),
                                float(total_delta - sum((D(row[3]) for row in revenues), Decimal(0))),
                                float(profit_total_delta - sum((D(row[3]) for row in profits), Decimal(0))),
                                float(100 * (bitcoin1 / bitcoin0 - 1))]]}


QUARTER_SQL = """WITH periods AS (
 SELECT period_end, MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,
 MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,
 MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,
 MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh
 FROM financials WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY period_end
), quarters AS (
 SELECT CAST(substr(period_end,1,4) AS INTEGER)+1 fiscal_year,1 quarter,rh-r2 revenue,oh-o2 income FROM periods
 UNION ALL SELECT CAST(substr(period_end,1,4) AS INTEGER)+1,2,r2,o2 FROM periods
) SELECT fiscal_year,quarter,revenue revenue_usd_million,income operating_income_usd_million,
100.0*income/revenue operating_margin_pct FROM quarters"""
QUARTER_RECONCILIATION_SQL = """WITH p AS (
 SELECT period_end,MAX(CASE WHEN months=3 AND measure='Total revenue' THEN amount END) r2,
 MAX(CASE WHEN months=6 AND measure='Total revenue' THEN amount END) rh,
 MAX(CASE WHEN months=3 AND measure='Operating income' THEN amount END) o2,
 MAX(CASE WHEN months=6 AND measure='Operating income' THEN amount END) oh
 FROM financials WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY period_end
) SELECT CAST(substr(period_end,1,4) AS INTEGER)+1 fiscal_year,
(rh-r2)+r2-rh revenue_residual_usd_million,(oh-o2)+o2-oh operating_income_residual_usd_million,
10000.0*(o2/r2-(oh-o2)/(rh-r2)) margin_qoq_bps FROM p"""
GUIDANCE_SQL = """SELECT a.business, a.constant_currency_percent actual_cc_pct,g.low guidance_low_pct,
g.high guidance_high_pct,a.constant_currency_percent-(g.low+g.high)/2.0 midpoint_gap_pp
FROM growth a JOIN guidance g ON a.business=g.business WHERE g.issue_date='2024-10-30'
AND g.fiscal_period='Q2FY2025' AND g.basis='constant_currency'"""
COVERAGE_SQL = """SELECT DISTINCT report_date,cash_equivalents_usd+us_government_debt_usd reserves_usd,
issued_sbc,100.0*(cash_equivalents_usd+us_government_debt_usd)/issued_sbc coverage_pct,
cash_equivalents_usd+us_government_debt_usd-reported_reserve_fv_usd residual_usd
FROM reserve_reports WHERE report_date IN ('2025-05-31','2025-06-30')"""
LAG_SQL = """SELECT DISTINCT report_date,report_signed_date,
CAST(julianday(report_signed_date)-julianday(report_date) AS INTEGER) days_to_signature
FROM reserve_reports WHERE report_date IN ('2025-05-31','2025-06-30')"""
RESERVE_BRIDGE_SQL = """WITH r AS (SELECT DISTINCT * FROM reserve_reports)
SELECT p.report_date prior_date,c.report_date current_date,
c.cash_equivalents_usd-p.cash_equivalents_usd cash_change_usd,
c.us_government_debt_usd-p.us_government_debt_usd debt_change_usd,
(c.cash_equivalents_usd+c.us_government_debt_usd)-(p.cash_equivalents_usd+p.us_government_debt_usd) reserve_change_usd,
c.issued_sbc-p.issued_sbc circulation_change_sbc,
10000.0*((c.cash_equivalents_usd+c.us_government_debt_usd)*1.0/c.issued_sbc-
(p.cash_equivalents_usd+p.us_government_debt_usd)*1.0/p.issued_sbc) coverage_change_bps
FROM r p CROSS JOIN r c WHERE p.report_date='2025-05-31' AND c.report_date='2025-06-30'"""
REVENUE_BRIDGE_SQL = """WITH p AS (SELECT category,
 MAX(CASE WHEN period_end='2023-12-31' THEN amount END) prior,
 MAX(CASE WHEN period_end='2024-12-31' THEN amount END) current
 FROM revenues WHERE months=12 AND period_end IN ('2023-12-31','2024-12-31') GROUP BY category),
t AS (SELECT prior,current FROM p WHERE category='Total net revenue')
SELECT CASE p.category WHEN 'Transaction-based revenue' THEN 'transaction' WHEN 'Subscription and services-based revenue'
THEN 'subscription' WHEN 'Hardware revenue' THEN 'hardware' ELSE 'bitcoin' END category,
p.prior revenue_2023_usd_thousand,p.current revenue_2024_usd_thousand,p.current-p.prior change_usd_thousand,
100.0*(p.current-p.prior)/(t.current-t.prior) contribution_pct,
100.0*p.prior/t.prior share_2023_pct,100.0*p.current/t.current share_2024_pct,
100.0*p.current/t.current-100.0*p.prior/t.prior share_change_pp
FROM p CROSS JOIN t WHERE p.category!='Total net revenue'"""
PROFIT_BRIDGE_SQL = """WITH components AS (
 SELECT period_end,replace(category,' revenue','') name,amount signed_amount FROM revenues
 WHERE months=12 AND category!='Total net revenue'
 UNION ALL SELECT period_end,replace(category,' costs',''),-amount FROM costs WHERE months=12 AND category!='Total cost of revenue'),
p AS (SELECT name,SUM(CASE WHEN period_end='2023-12-31' THEN signed_amount ELSE 0 END) prior,
SUM(CASE WHEN period_end='2024-12-31' THEN signed_amount ELSE 0 END) current FROM components
WHERE period_end IN ('2023-12-31','2024-12-31') GROUP BY name)
SELECT CASE name WHEN 'Transaction-based' THEN 'transaction' WHEN 'Subscription and services-based' THEN 'subscription'
WHEN 'Hardware' THEN 'hardware' WHEN 'Bitcoin' THEN 'bitcoin' ELSE 'acquired_technology_amortization' END category,
prior gross_profit_2023_usd_thousand,current gross_profit_2024_usd_thousand,current-prior change_usd_thousand FROM p"""
BLOCK_RECONCILIATION_SQL = """WITH totals AS (
 SELECT period_end,amount revenue FROM revenues WHERE months=12 AND category='Total net revenue'),
 c AS (SELECT period_end,amount cost FROM costs WHERE months=12 AND category='Total cost of revenue'),
 r AS (SELECT period_end,SUM(amount) amount FROM revenues WHERE months=12 AND category!='Total net revenue' GROUP BY period_end),
 s AS (SELECT period_end,SUM(amount) amount FROM costs WHERE months=12 AND category!='Total cost of revenue' GROUP BY period_end),
 b AS (SELECT v.period_end,v.amount-k.amount gp FROM revenues v JOIN costs k ON v.period_end=k.period_end
AND v.months=k.months WHERE v.months=12 AND v.category='Bitcoin revenue' AND k.category='Bitcoin costs'),
 p AS (SELECT t.period_end,t.revenue,c.cost,r.amount component_revenue,s.amount component_cost,b.gp
 FROM totals t JOIN c USING(period_end) JOIN r USING(period_end) JOIN s USING(period_end) JOIN b USING(period_end))
SELECT n.revenue-o.revenue revenue_change_usd_thousand,(n.revenue-n.cost)-(o.revenue-o.cost) gross_profit_change_usd_thousand,
(n.revenue-o.revenue)-(n.component_revenue-o.component_revenue) revenue_residual_usd_thousand,
((n.revenue-n.cost)-(o.revenue-o.cost))-((n.component_revenue-n.component_cost)-(o.component_revenue-o.component_cost)) gross_profit_residual_usd_thousand,
100.0*(n.gp/o.gp-1) bitcoin_gross_profit_growth_pct FROM p n CROSS JOIN p o WHERE n.period_end='2024-12-31' AND o.period_end='2023-12-31'"""


def specifications():
    a_tables = {
        'quarter_model': table({'fiscal_year': INTEGER, 'quarter': INTEGER, 'revenue_usd_million': numeric('usd_million'),
            'operating_income_usd_million': numeric('usd_million'), 'operating_margin_pct': numeric('percent')}, ['fiscal_year','quarter'], [['a03:s02','a03:s03']]),
        'quarter_reconciliation': table({'fiscal_year': INTEGER, 'revenue_residual_usd_million': numeric('usd_million'),
            'operating_income_residual_usd_million': numeric('usd_million'), 'margin_qoq_bps': numeric('basis_points')}, ['fiscal_year'], [['a03:s02','a03:s03']]),
        'guidance_bridge': table({'business': TEXT, 'actual_cc_pct': numeric('percent'), 'guidance_low_pct': numeric('percent'),
            'guidance_high_pct': numeric('percent'), 'midpoint_gap_pp': numeric('percentage_points')}, ['business'], [['a03:s01','a03:s04']])}
    b_tables = {
        'reserve_coverage': table({'report_date': TEXT, 'reserves_usd': numeric('usd'), 'issued_sbc': INTEGER,
            'coverage_pct': numeric('percent'), 'residual_usd': numeric('usd')}, ['report_date'], [['b01:s01','b01:s02']]),
        'signature_lag': table({'report_date': TEXT, 'report_signed_date': TEXT, 'days_to_signature': INTEGER}, ['report_date'], [['b01:s03','b01:s04']]),
        'reserve_bridge': table({'prior_date': TEXT,'current_date': TEXT,'cash_change_usd': numeric('usd'),
            'debt_change_usd': numeric('usd'),'reserve_change_usd': numeric('usd'),'circulation_change_sbc': INTEGER,
            'coverage_change_bps': numeric('basis_points')}, ['prior_date','current_date'], [['b01:s01','b01:s02']])}
    c_tables = {
        'revenue_bridge': table({'category': TEXT,'revenue_2023_usd_thousand': numeric('usd_thousand'),
            'revenue_2024_usd_thousand': numeric('usd_thousand'),'change_usd_thousand': numeric('usd_thousand'),
            'contribution_pct': numeric('percent'),'share_2023_pct': numeric('percent'),'share_2024_pct': numeric('percent'),
            'share_change_pp': numeric('percentage_points')}, ['category'], [['c03:s01']]),
        'profit_bridge': table({'category': TEXT,'gross_profit_2023_usd_thousand': numeric('usd_thousand'),
            'gross_profit_2024_usd_thousand': numeric('usd_thousand'),'change_usd_thousand': numeric('usd_thousand')}, ['category'], [['c03:s01','c03:s02']]),
        'reconciliation': table({'revenue_change_usd_thousand': numeric('usd_thousand'),'gross_profit_change_usd_thousand': numeric('usd_thousand'),
            'revenue_residual_usd_thousand': numeric('usd_thousand'),'gross_profit_residual_usd_thousand': numeric('usd_thousand'),
            'bitcoin_gross_profit_growth_pct': numeric('percent')}, ['revenue_change_usd_thousand'], [['c03:s01','c03:s02']])}
    return {
      'a01': {'source': 'a03', 'calculate': microsoft, 'tables': a_tables,
        'sql': {'quarter_model': QUARTER_SQL, 'quarter_reconciliation': QUARTER_RECONCILIATION_SQL, 'guidance_bridge': GUIDANCE_SQL},
        'claims': {'azure_within_earlier_range': {'verdict':'supported','evidence':[['a03:s01','a03:s04']]},
                   'q2_operating_margin_improved_from_q1': {'verdict':'contradicted','evidence':[['a03:s02','a03:s03']]},
                   'azure_operating_income_identifiable': {'verdict':'unresolved','evidence':[['a03:s05','a03:s06']]}},
        'request': 'Update the existing fiscal-quarter SQL model for Microsoft FY2025 Q2. Preserve the FY2024 quarters and the existing FY2025 Q1 outputs on their disclosed comparable basis. Reconcile quarter totals to six-month statements, calculate the sequential operating-margin change for each fiscal year, and compare Azure constant-currency growth with the earlier Q2 guidance range. Do not treat Intelligent Cloud as Azure operating income.',
        'rationale': 'An analyst needs an updated comparable quarterly model, a reconciliation and an actual-versus-guidance check. Dependencies are duration reconstruction, fiscal calendar, ratios, currency basis and segment scope. Using six-month amounts as a quarter, summing percentage changes or equating a segment with one business are plausible wrong methods.'},
      'b01': {'source': 'b01', 'calculate': brale, 'tables': b_tables,
        'sql': {'reserve_coverage': COVERAGE_SQL, 'signature_lag': LAG_SQL, 'reserve_bridge': RESERVE_BRIDGE_SQL},
        'claims': {'base_coverage_sql_is_valid': {'verdict':'contradicted','evidence':[['b01:s01','b01:s02','b01:s05']]},
                   'signature_lag_sql_is_valid': {'verdict':'supported','evidence':[['b01:s03','b01:s04']]},
                   'observations_identify_payments_volume': {'verdict':'unresolved','evidence':[['b01:s05']]}},
        'request': 'Audit the supplied SBC research SQL against the two reserve reports. Diagnose which starting calculations need repair and which are valid. Deliver coverage and residuals by economic observation date, preserve the valid signature-lag calculation, and bridge the cash, government-debt, reserve and circulation changes from May to June. Treat repeated identical exports as one report, while preserving different economic dates even when their amounts are equal. Determine whether these snapshots identify payments volume.',
        'rationale': 'A researcher needs to distinguish an economic date join defect from a valid signature-date calculation. The coverage module deliberately contains an authored synthetic join defect over authentic observations. Stock changes are useful, but are not transaction flows or evidence of historical publication timing.'},
      'c01': {'source': 'c03', 'calculate': block, 'tables': c_tables,
        'sql': {'revenue_bridge': REVENUE_BRIDGE_SQL, 'profit_bridge': PROFIT_BRIDGE_SQL, 'reconciliation': BLOCK_RECONCILIATION_SQL},
        'claims': {'bitcoin_majority_of_total_revenue_increase': {'verdict':'contradicted','evidence':[['c03:s01']]},
                   'all_components_reconcile': {'verdict':'supported','evidence':[['c03:s01','c03:s02']]},
                   'bitcoin_price_effect_identifiable': {'verdict':'unresolved','evidence':[['c03:s03']]}},
        'request': 'Complete an annual consolidated revenue and gross-profit attribution for Block using the FY2024 filing and its own FY2023 comparator. Audit the starting attribution. Show each revenue category\'s change, contribution to total revenue growth, annual shares and share change. Build a gross-profit bridge including acquired-technology amortization, reconcile both bridges to reported totals, and quantify Bitcoin gross-profit growth. Determine whether Bitcoin explains a majority of consolidated revenue growth and whether a separate price effect is identifiable.',
        'rationale': 'The analytical decision concerns growth attribution rather than annual mix. Dependencies include scope, contribution denominators, cost matching, the negative amortization component, residuals and the limits of price/volume attribution. The starting share-versus-contribution defect is authored, not a claimed vendor bug.'}}


def controls(key, original):
    scaled = copy.deepcopy(original)
    for rows in scaled.values():
        for row in rows:
            for field in row:
                if (field == 'amount' and row.get('unit') != 'million_shares') or field in {'issued_sbc','cash_equivalents_usd','us_government_debt_usd','reported_reserve_fv_usd'}:
                    row[field] *= 2
    result = [('scaled_amounts_preserve_ratios', scaled)]
    changed = copy.deepcopy(original)
    if key == 'a01':
        for row in changed['financials']:
            if row['period_end'] == '2024-12-31':
                changes = {'Revenue - Product':500, 'Total revenue':500, 'Gross margin':500,
                           'Sales and marketing':600, 'Operating income':-100,
                           'Income before income taxes':-100, 'Net income':-100}
                row['amount'] += changes.get(row['measure'],0)
        for duration in (3,6):
            rows = {row['measure']:row for row in changed['financials'] if row['period_end']=='2024-12-31' and row['months']==duration}
            for basis in ('Basic','Diluted'):
                rows['EPS - '+basis]['amount'] = float((D(rows['Net income']['amount']) / D(rows['Shares - '+basis]['amount'])).quantize(Decimal('0.01')))
        result.append(('current_quarter_changes_prior_quarter_preserved', changed))
    elif key == 'b01':
        for row in changed['reserve_reports']:
            if row['report_date'] == '2025-06-30':
                row['cash_equivalents_usd'] += 200000
                row['reported_reserve_fv_usd'] += 200000
        result.append(('june_cash_and_total_reserves_change', changed))
        duplicate = copy.deepcopy(original)
        duplicate['reserve_reports'].append(copy.deepcopy(duplicate['reserve_reports'][0]))
        result.append(('identical_export_duplicate', duplicate))
        equal = copy.deepcopy(original)
        for field in ('issued_sbc','cash_equivalents_usd','us_government_debt_usd','reported_reserve_fv_usd'):
            equal['reserve_reports'][1][field] = equal['reserve_reports'][0][field]
        result.append(('distinct_dates_with_equal_amounts', equal))
        return result
    else:
        for rows in changed.values():
            for row in rows:
                if row['period_end'] == '2024-12-31':
                    if row['category'] in {'Bitcoin revenue','Total net revenue'}: row['amount'] += 500000
                    if row['category'] in {'Bitcoin costs','Total cost of revenue'}: row['amount'] += 450000
        result.append(('bitcoin_revenue_and_cost_change_with_matching_totals', changed))
    later = copy.deepcopy(original)
    for name in ('financials',) if key == 'a01' else ('revenues','costs'):
        later[name] += [{**row, 'period_end':'2025-12-31'} for row in original[name] if row['period_end']=='2024-12-31']
    result.append(('irrelevant_later_disclosure', later))
    return result


def build_database(template, path, data):
    shutil.copyfile(template, path)
    connection = sqlite3.connect(path)
    for name, rows in data.items():
        connection.execute('DELETE FROM [' + name + ']')
        for row in rows:
            connection.execute('INSERT INTO [' + name + '] VALUES (' + ','.join('?' for _ in row) + ')', tuple(row.values()))
    connection.commit()
    connection.close()


def construct(destination):
    specs = specifications()
    manifest = {'dataset_id':'workflow-v1','scorer_version':'workflow-1.0.0',
                'status':'Three development prototypes, not expanded or calibrated',
                'execution_profile':'local-lima','tasks':{},'hashes':{}}
    item = {'type':'object','additionalProperties':False,'required':['id','file','evidence'],
            'properties':{'id':{'type':'string'},'file':{'type':'string'},'evidence':{'type':'array','items':{'type':'string'},'uniqueItems':True,'maxItems':20}}}
    claim = {'type':'object','additionalProperties':False,'required':['id','verdict','evidence'],
             'properties':{'id':{'type':'string'},'verdict':{'enum':['supported','contradicted','unresolved']},
                           'evidence':item['properties']['evidence'],'note':{'type':'string','maxLength':1024}}}
    schema = {'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','additionalProperties':False,
              'required':['task_id','tables','claims'],'properties':{'task_id':{'type':'string'},
              'tables':{'type':'array','minItems':1,'maxItems':4,'items':item},'claims':{'type':'array','minItems':1,'maxItems':4,'items':claim}}}
    for key, spec in specs.items():
        origin_manifest, origin, source = load(ROOT, task=spec['source'])
        task = destination / 'tasks' / key
        for folder in ('environment','tests','solution'):
            (task / folder).mkdir(parents=True)
        data = observations(source / 'environment/data.sqlite')
        identifier = 'workflow-v1-' + key
        source_text = (source / 'environment/sources.md').read_text()
        source_text += '\n## Source-derived observation tables\n\nThese are faithful normalized source observations, not target calculations.\n'
        for name, rows in data.items():
            source_text += '\n' + name + '\n' + json.dumps(rows,indent=2) + '\n'
        for folder in ('environment','tests'):
            shutil.copyfile(source / 'environment/data.sqlite', task / folder / 'data.sqlite')
            shutil.copyfile(source / 'environment/evidence.json', task / folder / 'evidence.json')
            (task / folder / 'sources.md').write_text(source_text)
            write_json(task / folder / 'schema.json', schema)
        public_tables = {name:{field:value for field,value in declaration.items() if field!='evidence'} for name,declaration in spec['tables'].items()}
        assertions = {
          'azure_within_earlier_range':'Azure Q2 FY2025 constant-currency growth lies within the closed range disclosed in the earlier Q1 call.',
          'q2_operating_margin_improved_from_q1':'Microsoft consolidated Q2 FY2025 operating margin exceeded its Q1 FY2025 operating margin.',
          'azure_operating_income_identifiable':'The supplied disclosures identify a separate amount of Azure operating income.',
          'base_coverage_sql_is_valid':'The supplied starting_reserve_coverage.sql correctly measures coverage separately at each requested economic observation date.',
          'signature_lag_sql_is_valid':'The supplied starting_signature_lag.sql correctly measures calendar days from economic observation date to signature date.',
          'observations_identify_payments_volume':'The supplied month-end reserve and circulation snapshots identify SBC payments volume during June.',
          'bitcoin_majority_of_total_revenue_increase':'Bitcoin contributed more than half of the increase in annual consolidated Block revenue from FY2023 to FY2024.',
          'all_components_reconcile':'The supplied revenue categories and cost categories, including acquired-technology amortization, reconcile to the reported annual consolidated totals.',
          'bitcoin_price_effect_identifiable':'The supplied disclosures identify a separate numerical Bitcoin price contribution to the annual revenue change.'}
        definitions = {'quarter_reconciliation':'Residuals are reconstructed quarterly sums less six-month reported totals. margin_qoq_bps is Q2 operating margin less Q1, in basis points.',
                       'guidance_bridge':'midpoint_gap_pp is actual constant-currency percent less the midpoint of the earlier guidance range.',
                       'reserve_coverage':'Coverage compares same-date cash plus government debt with issued SBC. Residual is component reserves less reported reserve fair value.',
                       'reserve_bridge':'Changes are June less May stocks, not transaction flows. Signature lags are calendar days, not known publication delays.',
                       'revenue_bridge':'Contribution is the category change divided by consolidated revenue change, in percent. share_change_pp is annual share in FY2024 less FY2023.',
                       'profit_bridge':'Amortization is a negative gross-profit component without a corresponding revenue category.',
                       'reconciliation':'Each residual is reported consolidated total change less summed component changes. Bitcoin gross-profit growth uses FY2023 as the base.'}
        write_json(task / 'environment/output_contract.json', {'tables':public_tables,
             'claim_assertions':{name:assertions[name] for name in spec['claims']},
             'definitions':{name:description for name,description in definitions.items() if name in spec['tables']}})
        starting = dict(spec['sql'])
        if key == 'a01':
            starting['quarter_model'] += " WHERE fiscal_year=2024 OR quarter=1"
        elif key == 'b01':
            starting['reserve_coverage'] = "SELECT r.report_date,SUM(a.cash_equivalents_usd+a.us_government_debt_usd) reserves_usd,r.issued_sbc,100.0*SUM(a.cash_equivalents_usd+a.us_government_debt_usd)/r.issued_sbc coverage_pct,SUM(a.cash_equivalents_usd+a.us_government_debt_usd)-r.reported_reserve_fv_usd residual_usd FROM reserve_reports r CROSS JOIN reserve_reports a GROUP BY r.report_date"
        else:
            starting['revenue_bridge'] = starting['revenue_bridge'].replace('100.0*(p.current-p.prior)/(t.current-t.prior) contribution_pct', '100.0*p.current/t.current-100.0*p.prior/t.prior contribution_pct')
        for name, sql in starting.items():
            (task / 'environment' / ('starting_' + name + '.sql')).write_text(sql + '\n')
        gold = {'task_id':identifier,'scorer_version':'workflow-1.0.0','tables':copy.deepcopy(spec['tables']),
                'claims':spec['claims'],'controls':[],'hashes':{}}
        direct = spec['calculate'](data)
        for name, rows in direct.items():
            gold['tables'][name]['rows'] = rows
        for number, (name, changed) in enumerate(controls(key,data),1):
            database = f'control-{number}.sqlite'
            build_database(source / 'environment/data.sqlite', task / 'tests' / database, changed)
            gold['controls'].append({'name':name,'database':database,'origin':'authored_synthetic_counterfactual',
                                     'tables':spec['calculate'](changed)})
        package = task / 'tests/workpaperbench'
        package.mkdir()
        for name in ('__init__.py','grading.py','workflow_grading.py','workflow_sql_worker.py','challenge_sql_worker.py'):
            shutil.copyfile(ROOT / 'workpaperbench' / name, package / name)
        (task / 'tests/Dockerfile').write_bytes((source / 'tests/Dockerfile').read_bytes())
        (task / 'tests/docker-compose.yaml').write_bytes((source / 'tests/docker-compose.yaml').read_bytes())
        verifier = (source / 'tests/verify.py').read_text().replace('workpaperbench.challenge_grading','workpaperbench.workflow_grading')
        (task / 'tests/verify.py').write_text(verifier)
        (task / 'tests/test.sh').write_text('#!/bin/bash\nset -euo pipefail\npython /tests/verify.py\n')
        gold['hashes'] = {path.relative_to(task / 'tests').as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (task / 'tests').rglob('*') if path.is_file()}
        write_json(task / 'tests/gold.json',gold)
        reference = {'task_id':identifier,'tables':[{'id':name,'file':name+'.sql','evidence':declaration['evidence'][0]} for name,declaration in spec['tables'].items()],
                     'claims':[{'id':name,'verdict':declaration['verdict'],'evidence':declaration['evidence'][0]} for name,declaration in spec['claims'].items()]}
        write_json(task / 'tests/reference.json',reference)
        solution = '#!/bin/bash\nset -euo pipefail\n'
        for name, sql in spec['sql'].items():
            (task / 'solution' / (name + '.sql')).write_text(sql + '\n')
            solution += "cat > /logs/artifacts/" + name + ".sql <<'SQL'\n" + sql + '\nSQL\n'
        solution += "cat > /logs/artifacts/answer.json <<'ANSWER'\n" + json.dumps(reference,indent=2) + '\nANSWER\n'
        (task / 'solution/solve.sh').write_text(solution)
        files = ' '.join(['data.sqlite','evidence.json','sources.md','schema.json','output_contract.json', *('starting_'+name+'.sql' for name in starting)])
        dockerfile = (source / 'environment/Dockerfile').read_text().split('COPY ',1)[0] + 'COPY ' + files + ' /workspace/\n'
        (task / 'environment/Dockerfile').write_text(dockerfile)
        (task / 'task.toml').write_text((source / 'task.toml').read_text().replace('challenge-v2-'+spec['source'],identifier))
        instruction = '# Financial workflow\n\n' + spec['request'] + '\n\n'
        instruction += 'Read the source headings, definitions and evidence locators in /workspace/sources.md and evidence.json. The SQLite tables contain source-derived observations. The starting SQL is an authored research work product. Its defects are synthetic, not discovered issuer defects.\n\n'
        instruction += 'Deliver /logs/artifacts/answer.json and one read-only SELECT/CTE .sql file per requested named table. The JSON schema is /workspace/schema.json and the public columns, units, keys and claim assertions are /workspace/output_contract.json. Use the literal claim IDs for the assertions stated there, with supported, contradicted or unresolved verdicts. A short optional note is not semantically graded. Cite each output\'s supporting evidence IDs.\n\n'
        instruction += 'Table column names are required, column order and row order are ignored. Keys are unique, duplicate output keys fail, and no row may be silently dropped. Ratios labeled percent must be multiplied by 100, and basis points by 10000. Monetary columns retain the specified units. Each query returns at most 100 rows and 16 columns, with no file access, DDL, writes, wall-clock dates or extensions. Answer JSON is at most 65536 bytes and each SQL file at most 16384 UTF-8 bytes. No additional artifact files.\n\n'
        instruction += 'Recompute from pristine inputs. Hidden synthetic controls exercise the declared period filters, equivalent monetary scaling, meaningful component changes and unaffected outputs. SBC also tests duplicate exports and distinct economic dates with equal amounts. Required categories for Block are transaction, subscription, hardware, bitcoin and acquired_technology_amortization in the profit bridge. FY2024 and FY2025 each have fiscal quarters 1 and 2 in the Microsoft model.\n\nTask ID: ' + identifier + '\n'
        (task / 'instruction.md').write_text(instruction)
        write_json(task / 'authoring.json', {'rationale':spec['rationale'],'source_group':origin['source_group'],
                   'source_catalog':origin_manifest['manifest_id'],'source_task_sha256':origin['task_sha256'],
                   'split':'development','exposure':'Previously published source group, never held out',
                   'observations':'authentic permitted capture','starting_defects':'authored synthetic work-product defects',
                   'controls':'authored synthetic counterfactuals','reference_method':'Independent Python Decimal calculations from source rows, separate from submitted SQL',
                   'human_review':'pending'})
        manifest['tasks'][key] = {'task_id':identifier,'path':'datasets/workflow-v1/tasks/'+key,
                                 'task_sha256':tree_hash(task),'split':'development','source_group':origin['source_group']}
    for name in ('scripts/build_workflow_tasks.py','workpaperbench/workflow_grading.py','workpaperbench/workflow_sql_worker.py','workpaperbench/challenge_sql_worker.py','workpaperbench/grading.py'):
        manifest['hashes'][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    manifest['scorer_path'] = 'workpaperbench/workflow_grading.py'
    manifest['scorer_sha256'] = manifest['hashes'][manifest['scorer_path']]
    manifest['content_hash'] = content_hash(manifest)
    manifest['manifest_id'] = 'workflow-v1-canonical-' + manifest['content_hash'][:12]
    write_json(destination / 'manifest.json',manifest)
    return manifest


def build(check):
    destination = ROOT / 'datasets/workflow-v1'
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary)
        manifest = construct(staged)
        for path in staged.rglob('*'):
            if not path.is_file(): continue
            target = destination / path.relative_to(staged)
            if check:
                if not target.is_file() or path.read_bytes() != target.read_bytes():
                    raise ValueError('workflow_reconstruction_mismatch:' + str(target))
            else:
                if target.exists() and path.read_bytes() != target.read_bytes():
                    raise ValueError('workflow_preview_already_exists')
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(path.read_bytes())
    print(manifest['manifest_id'],len(manifest['tasks']),'development prototypes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    build(parser.parse_args().check)
