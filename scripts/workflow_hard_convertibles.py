"""Veeco contractual settlement and diluted-EPS development case."""
import copy
from decimal import Decimal


def d(value):
    return Decimal(str(value))


def instruments(data, price):
    terms = {r['note']: r for r in data['contract_terms']}
    result = []
    for row in data['notes']:
        term = terms[row['note']]
        full = d(row['principal']) * d(term['conversion_rate']) / 1000
        mandatory = term['principal_settlement'] == 'cash'
        shares = max(d(0), full - d(row['principal']) / price) if mandatory else full
        adjustment = d(0) if mandatory else d(row['coupon']) + d(row['amortization'])
        result.append((row['note'], shares, adjustment, full, mandatory))
    return result


def calculate(data):
    """Use incremental EPS ordering, independently of the subset SQL reference."""
    basis = data['eps_basis'][0]
    basic, awards = d(basis['basic_shares']), d(basis['award_shares'])
    notes = {r['note']: r for r in data['notes']}
    settlement, earnings = [], []
    for scenario in data['price_cases']:
        price = d(scenario['price'])
        items = instruments(data, price)
        for name, excess, _, full, mandatory in items:
            face = d(notes[name]['principal'])
            converts = full * price > face
            cash = face if mandatory or not converts else d(0)
            issued = excess if mandatory else full if converts else d(0)
            settlement.append([scenario['price_case'], name, float(cash), float(issued)])
        ranked = sorted((x for x in items if x[1] > 0), key=lambda x: (x[2] / x[1], x[0]))
        for scenario_income in data['income_cases']:
            income = d(scenario_income['income'])
            numerator, denominator = income, basic + awards
            for _, shares, adjustment, _, _ in ranked:
                if adjustment * denominator < numerator * shares:
                    numerator += adjustment
                    denominator += shares
            earnings.append([scenario['price_case'], scenario_income['income_case'],
                             float(income / basic), float(numerator / denominator)])
    query = data['threshold_case'][0]
    items = instruments(data, d(query['price']))
    thresholds = []
    for name, shares, adjustment, _, mandatory in items:
        if mandatory:
            continue
        ratio = adjustment / shares
        earlier = [x for x in items if x[1] > 0 and x[2] / x[1] < ratio]
        boundary = ratio * (basic + awards + sum((x[1] for x in earlier), d(0)))
        boundary -= sum((x[2] for x in earlier), d(0))
        thresholds.append(['earnings_' + name, float(boundary)])
    full_total = sum((x[3] for x in items), d(0))
    choice_total = sum((x[3] for x in items if not x[4]), d(0))
    cash_face = sum((d(notes[x[0]]['principal']) for x in items if x[4]), d(0))
    target = d(query['target_shares'])
    assert choice_total < target < full_total, 'target must fall in the continuous excess-share regime'
    thresholds.append(['share_price', float(cash_face / (full_total - target))])
    return {'settlement_scenarios': settlement, 'diluted_eps': earnings, 'thresholds': thresholds}


INPUT_CTE = """WITH instruments AS (
 SELECT n.*,t.conversion_rate,t.principal_settlement,
 n.principal*t.conversion_rate/1000.0 full_shares
 FROM notes n JOIN contract_terms t USING(note)
) """
EPS_CTE = INPUT_CTE + """, components AS (
 SELECT p.price_case,n.note,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)
 ELSE full_shares END shares,
 CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment,
 ROW_NUMBER() OVER(PARTITION BY p.price_case ORDER BY n.note) position
 FROM instruments n CROSS JOIN price_cases p
) """
SQL = {
    'settlement_scenarios': INPUT_CTE + """SELECT p.price_case,n.note,
 CASE WHEN principal_settlement='cash' OR full_shares*p.price<=principal
 THEN principal ELSE 0.0 END cash_usd_million,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)
 WHEN full_shares*p.price>principal THEN full_shares ELSE 0.0 END gross_shares_million
 FROM instruments n CROSS JOIN price_cases p""",
    'diluted_eps': EPS_CTE + """, masks(mask) AS (
 SELECT 0 UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
), candidates AS (
 SELECT c.price_case,i.income_case,i.income,b.basic_shares,m.mask,
 i.income+SUM(CASE WHEN (m.mask & (1 << (c.position-1)))!=0 THEN adjustment ELSE 0 END) numerator,
 b.basic_shares+b.award_shares+
 SUM(CASE WHEN (m.mask & (1 << (c.position-1)))!=0 THEN shares ELSE 0 END) denominator
 FROM components c CROSS JOIN income_cases i CROSS JOIN eps_basis b CROSS JOIN masks m
 GROUP BY c.price_case,i.income_case,i.income,b.basic_shares,b.award_shares,m.mask
) SELECT price_case,income_case,income/basic_shares basic_eps,
 MIN(numerator/denominator) diluted_eps FROM candidates
 GROUP BY price_case,income_case,income,basic_shares""",
    'thresholds': INPUT_CTE + """, components AS (
 SELECT note,principal_settlement,
 CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/q.price)
 ELSE full_shares END shares,
 CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment
 FROM instruments CROSS JOIN threshold_case q
), boundaries AS (
 SELECT c.note,c.adjustment/c.shares*(b.basic_shares+b.award_shares+
 COALESCE(SUM(o.shares),0))-COALESCE(SUM(o.adjustment),0) value
 FROM components c CROSS JOIN eps_basis b LEFT JOIN components o
 ON o.shares>0 AND o.adjustment*c.shares<c.adjustment*o.shares
 WHERE c.principal_settlement!='cash'
 GROUP BY c.note,c.adjustment,c.shares,b.basic_shares,b.award_shares
) SELECT 'earnings_'||note measure,value FROM boundaries UNION ALL
 SELECT 'share_price',SUM(CASE WHEN principal_settlement='cash' THEN principal ELSE 0 END)
 /(SUM(full_shares)-q.target_shares) FROM instruments CROSS JOIN threshold_case q
 GROUP BY q.target_shares""",
}


def alternatives():
    """Ordered prefix EPS and direct per-series settlement are equivalent routes."""
    result = dict(SQL)
    result['diluted_eps'] = EPS_CTE + """, ordered AS (
 SELECT price_case,note,shares,adjustment,
 SUM(shares) OVER(PARTITION BY price_case ORDER BY adjustment/shares,note
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) cumulative_shares,
 SUM(adjustment) OVER(PARTITION BY price_case ORDER BY adjustment/shares,note
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) cumulative_adjustment
 FROM components WHERE shares>0
), candidates AS (
 SELECT p.price_case,i.income_case,i.income/b.basic_shares basic_eps,
 i.income/(b.basic_shares+b.award_shares) eps
 FROM price_cases p CROSS JOIN income_cases i CROSS JOIN eps_basis b
 UNION ALL SELECT o.price_case,i.income_case,i.income/b.basic_shares,
 (i.income+cumulative_adjustment)/(b.basic_shares+b.award_shares+cumulative_shares)
 FROM ordered o CROSS JOIN income_cases i CROSS JOIN eps_basis b
) SELECT price_case,income_case,basic_eps,MIN(eps) diluted_eps
 FROM candidates GROUP BY price_case,income_case,basic_eps"""
    result['settlement_scenarios'] = INPUT_CTE + """, values_at_price AS (
 SELECT p.price_case,n.*,p.price,MAX(principal,full_shares*p.price) holder_value
 FROM instruments n CROSS JOIN price_cases p
), funding AS (
 SELECT *,CASE WHEN principal_settlement='cash' OR holder_value=principal
 THEN principal ELSE 0.0 END funded FROM values_at_price
) SELECT price_case,note,funded cash_usd_million,
 (holder_value-funded)/price gross_shares_million FROM funding"""
    return result


def declaration(columns, keys, evidence):
    result = {'columns': {}, 'keys': keys, 'row_order': 'ignored',
              'duplicates': 'Keys must be unique', 'evidence': evidence,
              'context_evidence_allowed': []}
    for name, unit in columns:
        result['columns'][name] = ({'type': 'text', 'unit': 'label'} if unit == 'label' else
                                   {'type': 'real', 'unit': unit,
                                    'tolerance': 1e-9 if unit == 'usd_per_share' else 1e-6})
    return result


def specification():
    support = ['b01:s01', 'b01:s03', 'b01:s04', 'b01:s05', 'b01:s08']
    eps_support = support + ['b01:s02', 'b01:s06', 'b01:s07']
    alternate_support = ['b01:s01', 'b01:s05', 'b01:s06', 'b01:s08']
    alternate_eps_support = alternate_support + ['b01:s02', 'b01:s07']
    return {
        'source': 'veeco-2024', 'calculate': calculate, 'sql': SQL,
        'title': 'Veeco conversion funding and earnings-dependent dilution',
        'nearest': ['workflow-v15/b09', 'workflow-v15/c08', 'workflow-hard-pilot-v1/b01'],
        'novelty': 'Derive cash and share settlement by instrument, distinguish maturity conversion economics from EPS potential shares, and find earnings inclusion boundaries after other dilutive instruments. Construct the portfolio denominator from conditional instruments instead of selecting an already supplied denominator or matching reported share bases.',
        'request': 'Assess Veeco consolidated convertible-note exposure using the December 31, 2024 capital structure. Calculate gross note settlement funding and share issuance across the authored maturity-price scenarios. Separately calculate basic and diluted EPS across the hypothetical price and earnings scenarios. Find the share price that reaches the specified gross-issuance target and the net-income neutrality boundary for each note with optional principal settlement at the threshold-case price. These are sensitivities of frozen inputs, not forecasts or a reconstruction of actual FY2024 EPS.',
        'assumptions': 'Authored scenarios: Freeze the disclosed year-end principal balances and use the indenture conversion rates in contract_terms, including 34.2185 for 2029. Preserve the 10-K rate observation separately. Assume no conversion-rate adjustments, make-whole events, early conversions or repurchases. Each maturity scenario applies its price at each note\'s own maturity and throughout every relevant observation day, not at one common maturity date. Holders choose conversion only when its value exceeds face and cash repayment at equality. For converted 2025 and 2027 notes the issuer elects physical share settlement. For 2029 it elects shares for the amount above mandatory cash principal. Ignore interest cash, fractional-share rounding and all separate capped-call positions. Report gross note issuance, not net company dilution. EPS is a separate hypothetical full period with all notes outstanding throughout. Use the disclosed basic weighted shares and incremental award shares as fixed inputs, regardless of scenario price. All income cases are positive income from continuing operations available to common shareholders, with no preferred dividends or discontinued operations. Preserve disclosed note coupon and amortization expense for numerator treatment with no additional tax adjustment. A neutrality boundary is the income where adding that issue has zero incremental EPS effect after accounting for other eligible issues. Grade the unique EPS value, not arbitrary tied inclusion witnesses.',
        'definitions': {
            'settlement_scenarios': 'One row for every price_case and note. Cash is positive principal or conversion cash funding in USD million. gross_shares_million is gross common shares issued under the authored maturity election. Neither value is the debt carrying amount or a GAAP diluted share count.',
            'diluted_eps': 'One row per price_case and income_case. basic_eps and diluted_eps are USD per share. Fixed award shares affect dilution and do not enter basic EPS. Return the greatest dilution consistent with the supplied accounting definitions. Equivalent inclusion choices at a neutrality tie are accepted because only EPS is graded.',
            'thresholds': 'Three rows. measure share_price has value in USD per share and is the price where aggregate gross note issuance reaches threshold_case.target_shares million. Measures earnings_2025 and earnings_2027 have value in USD million and identify the net-income neutrality boundary at threshold_case.price. These boundaries concern the complete note portfolio. Both endpoints of an EPS tie produce the same graded EPS.'},
        'tables': {
            'settlement_scenarios': declaration([('price_case','label'),('note','label'),('cash_usd_million','usd_million'),('gross_shares_million','million_shares')], ['price_case','note'], [support, alternate_support]),
            'diluted_eps': declaration([('price_case','label'),('income_case','label'),('basic_eps','usd_per_share'),('diluted_eps','usd_per_share')], ['price_case','income_case'], [eps_support, alternate_eps_support]),
            'thresholds': declaration([('measure','label'),('value','measure_dependent')], ['measure'], [eps_support, alternate_eps_support])},
        'claims': {
            'claim_1': {'assertion': 'At the authored USD 12 maturity price, no notes convert under the holder election, yet the EPS sensitivity at reported FY2024 net income includes dilution beyond fixed award shares.', 'verdict':'supported', 'evidence':[eps_support, alternate_eps_support]},
            'claim_2': {'assertion': 'The 2029 note principal can be settled entirely in shares under the supplied contractual terms.', 'verdict':'contradicted', 'evidence':[['b01:s05'],['b01:s06']]},
            'claim_3': {'assertion': 'Gross note shares equal net company share dilution after all capped-call transactions.', 'verdict':'unresolved', 'evidence':[['b01:s06','b01:s08']]}}
    }


def controls(original):
    out = []
    def add(name, rationale, mutate):
        changed = copy.deepcopy(original)
        mutate(changed)
        out.append((name, rationale, changed))
    def scale(data):
        for table, fields in {'notes':['principal','carrying','coupon','amortization'],
                              'eps_basis':['basic_shares','award_shares','reported_income','reported_note_addback'],
                              'income_cases':['income'], 'threshold_case':['target_shares']}.items():
            for row in data[table]:
                for field in fields:
                    row[field] *= 2
    add('scale', 'Double all principal, carrying, expense, share and earnings quantities, including the share target. Prices and EPS stay invariant.', scale)
    add('row_order', 'Reverse input rows without changing their financial identities.', lambda data: [rows.reverse() for rows in data.values()])
    def reverse(data):
        next(r for r in data['notes'] if r['note']=='2027')['amortization'] = 1.0
        data['eps_basis'][0]['reported_note_addback'] = 2.964
    add('dilution_order', 'A higher synthetic noncash expense on the 2027 series reverses incremental-EPS ordering. Face values and contractual conversion terms stay fixed.', reverse)
    def out_of_money(data):
        for row in data['price_cases']:
            row['price'] = 10.0
        data['threshold_case'][0]['price'] = 10.0
    add('out_of_money', 'All maturity conversions are out of the money, while full-share EPS treatment for issuer-choice notes still depends on income.', out_of_money)
    def carrying(data):
        for row in data['notes']:
            row['carrying'] *= 0.9
    add('carrying_only', 'A changed unamortized debt discount changes carrying value alone at the snapshot. Face obligations, fixed scenario expenses and all outputs remain unchanged.', carrying)
    def principal(data):
        row = next(r for r in data['notes'] if r['note']=='2029')
        factor = 250.0 / row['principal']
        for field in ['principal','carrying','coupon','amortization']:
            row[field] *= factor
        row['principal'] = 250.0
    add('cash_principal', 'A synthetic larger 2029 tranche scales its face, carrying value and expenses proportionately. Contract rates and the gross-share target stay fixed.', principal)
    add('target_shift', 'Change the authored target to six million gross shares, retaining a feasible continuous conversion-excess threshold.', lambda data: data['threshold_case'][0].update(target_shares=6.0))
    def tie(data):
        # Synthetic simple terms make all arithmetic at the first boundary exact.
        data['eps_basis'][0].update(basic_shares=10.0, award_shares=1.0)
        for row in data['contract_terms']:
            if row['note']=='2027':
                row['conversion_rate'] = 80.0
        for row in data['reported_rates']:
            if row['note']=='2027':
                row['conversion_rate'] = 80.0
        for row in data['notes']:
            if row['note']=='2027':
                row.update(coupon=1.0, amortization=0.0)
        data['eps_basis'][0]['reported_note_addback'] = 2.026
        for row in data['price_cases']:
            row['price'] = 10.0
        data['threshold_case'][0]['price'] = 10.0
        data['income_cases'][0]['income'] = 5.5
    add('neutrality_tie', 'Authored parameters make the 2027 issue exactly neutral at income 5.5 after 11 million base-plus-award shares. Including or excluding it yields the same graded EPS.', tie)
    return out


def mistakes():
    return {
        'carrying_as_face': {'table':'settlement_scenarios', 'sql':SQL['settlement_scenarios'].replace('n.principal*t.conversion_rate','n.carrying*t.conversion_rate').replace('THEN principal ELSE','THEN carrying ELSE'), 'rationale':'Carrying value is not the amount contractually repaid or converted.'},
        'all_principal_cash': {'table':'settlement_scenarios', 'sql':SQL['settlement_scenarios'].replace("principal_settlement='cash' OR full_shares*p.price<=principal",'1=1'), 'rationale':'Physical settlement of in-the-money issuer-choice notes need not fund their principal in cash.'},
        'all_notes_full_shares': {'table':'diluted_eps', 'sql':SQL['diluted_eps'].replace("CASE WHEN principal_settlement='cash' THEN MAX(0.0,full_shares-principal/p.price)\n ELSE full_shares END shares",'full_shares shares'), 'rationale':'Mandatory-cash 2029 principal cannot enter diluted EPS as full conversion shares.'},
        'maturity_choice_as_eps': {'table':'diluted_eps', 'sql':SQL['diluted_eps'].replace('ELSE full_shares END shares','ELSE CASE WHEN full_shares*p.price>principal THEN full_shares ELSE 0.0 END END shares'), 'rationale':'Full-share if-converted EPS is not conditioned on economic maturity conversion being in the money.'},
        'cash_principal_interest_addback': {'table':'diluted_eps', 'sql':SQL['diluted_eps'].replace("CASE WHEN principal_settlement='cash' THEN 0.0 ELSE coupon+amortization END adjustment",'coupon+amortization adjustment'), 'rationale':'The cash-principal 2029 series retains interest expense in the specified EPS treatment.'},
        'always_include': {'table':'diluted_eps', 'sql':SQL['diluted_eps'].replace('FROM candidates\n GROUP BY','FROM candidates WHERE mask=7\n GROUP BY'), 'rationale':'Positive income alone does not make every convertible issue dilutive.'},
        'standalone_eps': {'table':'diluted_eps', 'sql':EPS_CTE + """SELECT c.price_case,i.income_case,
 i.income/b.basic_shares basic_eps,
 (i.income+SUM(CASE WHEN adjustment*(b.basic_shares+b.award_shares)<i.income*shares
 THEN adjustment ELSE 0.0 END)) /
 (b.basic_shares+b.award_shares+SUM(CASE WHEN adjustment*(b.basic_shares+b.award_shares)<i.income*shares
 THEN shares ELSE 0.0 END)) diluted_eps
 FROM components c CROSS JOIN income_cases i CROSS JOIN eps_basis b
 GROUP BY c.price_case,i.income_case,i.income,b.basic_shares,b.award_shares""",
            'rationale':'An issue that is dilutive alone can become antidilutive once a lower incremental-EPS series is included.'},
        'standalone_boundary': {'table':'thresholds', 'sql':SQL['thresholds'].replace('ON o.shares>0 AND','ON 1=0 AND'), 'rationale':'Ignoring prior dilutive issues gives the wrong portfolio earnings neutrality boundary.'},
    }
