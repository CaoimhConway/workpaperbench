"""Contractual liquidity decisions for a springing fixed-charge covenant."""
import copy
from decimal import Decimal

D = lambda value: Decimal(str(value))


def parameters(data, row):
    f = data['facility'][0]
    capacity = D(f['commitment']) - D(f['utilised_including_lc'])
    trigger = D(f['covenant_availability']) - D(f['test_threshold'])
    rate = D(row['new_debt_cash_rate'])
    fixed = sum(D(row[k]) for k in ('scheduled_principal', 'existing_cash_interest', 'cash_tax', 'ordinary_dividend'))
    headroom = D(row['ebitda']) - D(row['net_cash_capex']) - fixed
    cash = headroom - D(row['working_capital_outflow'])
    assert capacity > 0 and trigger > 0 and 0 < rate < 1
    assert cash + (1-rate)*min(capacity, trigger) > 0
    return capacity, trigger, rate, fixed, headroom, cash


def calculate(data):
    proposals, frontiers, cures = [], [], []
    for row in data['planning_cases']:
        c, t, r, f, h, b = parameters(data, row)
        for p in data['proposals']:
            x = D(p['special_dividend'])
            d = max(D(0), (x-b)/(1-r))
            availability = D(data['facility'][0]['covenant_availability'])-d
            ratio = (h+f)/(f+r*d+x)
            tested = d >= t
            proposals.append([row['scenario'], p['proposal'], float(d), float(availability),
                              float(ratio), int(tested), int(d <= c and (not tested or ratio >= 1))])
        # The first region has an open right endpoint when the test can spring.
        endpoints = [(b+(1-r)*min(c,t), c < t)]
        if c >= t:
            for d in {t, c, max(t, min(c, h-b))}:
                value = min(b+(1-r)*d, h-r*d)
                if value >= 0:
                    endpoints.append((value, True))
        upper = max(x for x, _ in endpoints)
        frontiers.append([row['scenario'], float(upper), int(any(x == upper and a for x,a in endpoints))])
        for p in data['equity_targets']:
            x = D(p['special_dividend'])
            limit = min(c,t)
            gap = x-b-(1-r)*limit
            candidates = [(max(D(0),gap), c < t or gap < 0)]
            d = min(c,(h-x)/r)
            if d >= t:
                candidates.append((max(D(0),x-b-(1-r)*d), True))
            lower = min(e for e,_ in candidates)
            cures.append([row['scenario'],p['target'],float(lower),
                          int(any(e == lower and a for e,a in candidates))])
    return {'proposal_tests':proposals,'distribution_frontier':frontiers,'equity_support':cures}


BASE = """WITH p AS (
 SELECT s.*,f.commitment-f.utilised_including_lc capacity,
 f.covenant_availability-f.test_threshold trigger_draw,f.covenant_availability,
 scheduled_principal+existing_cash_interest+cash_tax+ordinary_dividend fixed_charges
 FROM planning_cases s CROSS JOIN facility f
), q AS (
 SELECT *,ebitda-net_cash_capex-fixed_charges h,
 ebitda-net_cash_capex-fixed_charges-working_capital_outflow b,
 new_debt_cash_rate r FROM p
) """

SQL = {
 'proposal_tests': BASE+""", proposed AS (
 SELECT q.*,v.*,MAX(0.0,(special_dividend-b)/(1-r)) draw FROM q CROSS JOIN proposals v
), tested AS (
 SELECT *, (ebitda-net_cash_capex)/(fixed_charges+r*draw+special_dividend) ratio FROM proposed
)
SELECT scenario,proposal,draw required_draw_usd_million,
 covenant_availability-draw covenant_availability_usd_million,ratio fixed_charge_ratio,
 CASE WHEN draw>=trigger_draw THEN 1 ELSE 0 END covenant_tested,
 CASE WHEN draw<=capacity AND (draw<trigger_draw OR ratio>=1) THEN 1 ELSE 0 END feasible FROM tested""",
 'distribution_frontier': BASE+""", vertices AS (
 SELECT scenario,trigger_draw d FROM q WHERE capacity>=trigger_draw
 UNION SELECT scenario,capacity FROM q WHERE capacity>=trigger_draw
 UNION SELECT scenario,MAX(trigger_draw,MIN(capacity,h-b)) FROM q WHERE capacity>=trigger_draw
), options AS (
 SELECT scenario,b+(1-r)*MIN(capacity,trigger_draw) value,
 CASE WHEN capacity<trigger_draw THEN 1 ELSE 0 END attained FROM q
 UNION ALL
 SELECT q.scenario,MIN(b+(1-r)*d,h-r*d),1 FROM q JOIN vertices USING(scenario)
 WHERE MIN(b+(1-r)*d,h-r*d)>=0
), best AS (SELECT scenario,MAX(value) value FROM options GROUP BY scenario)
SELECT b.scenario,b.value upper_limit_usd_million,MAX(o.attained) attainable
 FROM best b JOIN options o ON b.scenario=o.scenario AND ABS(b.value-o.value)<1e-9
 GROUP BY b.scenario,b.value""",
 'equity_support': BASE+""", required AS (
 SELECT q.*,v.*,MIN(capacity,(h-special_dividend)/r) active_draw,
 special_dividend-b-(1-r)*MIN(capacity,trigger_draw) gap FROM q CROSS JOIN equity_targets v
), options AS (
 SELECT scenario,target,MAX(0.0,gap) value,
 CASE WHEN capacity<trigger_draw OR gap<0 THEN 1 ELSE 0 END attained FROM required
 UNION ALL SELECT scenario,target,MAX(0.0,special_dividend-b-(1-r)*active_draw),1
 FROM required WHERE active_draw>=trigger_draw
), best AS (SELECT scenario,target,MIN(value) value FROM options GROUP BY scenario,target)
SELECT b.scenario,b.target,b.value lower_limit_usd_million,MAX(o.attained) attainable
 FROM best b JOIN options o ON b.scenario=o.scenario AND b.target=o.target AND ABS(b.value-o.value)<1e-9
 GROUP BY b.scenario,b.target,b.value"""}


def alternatives():
    # A closed-form envelope replaces the reference's branch vertex enumeration.
    result = dict(SQL)
    result['distribution_frontier'] = BASE+""", envelope AS (
 SELECT *,b+(1-r)*MIN(capacity,trigger_draw) inactive_limit,
 CASE WHEN capacity>=trigger_draw THEN
 MIN(b+(1-r)*capacity,h-r*trigger_draw,(1-r)*h+r*b) ELSE -1 END active_limit FROM q
)
SELECT scenario,MAX(inactive_limit,active_limit) upper_limit_usd_million,
 CASE WHEN capacity<trigger_draw OR active_limit>=inactive_limit THEN 1 ELSE 0 END attainable FROM envelope"""
    # For a fixed distribution, the admissible-draw set is a union of intervals.
    result['equity_support'] = BASE+""", limits AS (
 SELECT q.*,v.*,CASE WHEN capacity>=trigger_draw AND (h-special_dividend)/r>=trigger_draw
 THEN MIN(capacity,(h-special_dividend)/r) ELSE MIN(capacity,trigger_draw) END draw_limit,
 CASE WHEN capacity<trigger_draw OR (capacity>=trigger_draw AND (h-special_dividend)/r>=trigger_draw)
 THEN 1 ELSE 0 END closed FROM q CROSS JOIN equity_targets v
), gaps AS (SELECT *,special_dividend-b-(1-r)*draw_limit gap FROM limits)
SELECT scenario,target,MAX(0.0,gap) lower_limit_usd_million,
 CASE WHEN closed=1 OR gap<0 THEN 1 ELSE 0 END attainable FROM gaps"""
    return result


def table(columns, keys, evidence):
    return {'columns':{name:({'type':'text','unit':'label'} if kind=='text' else
            {'type':'integer','unit':'indicator'} if kind=='flag' else
            {'type':'real','unit':'ratio' if kind=='ratio' else 'usd_million','tolerance':1e-7})
            for name,kind in columns},'keys':keys,'row_order':'ignored','duplicates':'Keys must be unique',
            'evidence':evidence,'context_evidence_allowed':[]}


def specification():
    support = [['a01:s01','a01:s02','a01:s04'],['a01:s03','a01:s04']]
    return {
      'source':'ashtead-2025','calculate':calculate,'sql':SQL,
      'title':'Ashtead distributions under a springing fixed-charge covenant',
      'nearest':['workflow-v15/c10','workflow-hard-pilot-v1/c01'],
      'novelty':'Construct a joint cash-funding and contractual-covenant feasibility model. Borrowing finances distributions while adding cash interest and can activate a previously inapplicable test. Optimize across the resulting regimes and distinguish an achievable amount from an open-boundary limit.',
      'request':'Assess three explicitly hypothetical twelve-month funding cases using the Ashtead Group ABL terms and facility observations at April 30, 2025. Test the proposed special dividends without new equity, find the sharp upper limit on special dividends, and find the sharp lower limit on cash equity needed for each target distribution. Apply the disclosed covenant only when it is applicable. Report whether each limit is actually attainable. This is a conditional funding analysis, not a company forecast or legal authorization to pay dividends.',
      'assumptions':[
        'All amounts in facility, planning_cases, proposals and equity_targets are USD million, except new_debt_cash_rate, an annual decimal rate. facility contains source observations. The other tables are authored planning assumptions, not issuer forecasts.',
        'Use the disclosed covenant summary as the complete financial-performance test for this exercise. All other draw conditions are satisfied. No commitment increase, accordion, refinancing or alternative debt is available. Keep the separately reported covenant availability independent of unused commitment. Its difference from commitment less utilisation is not explained by the supplied extract.',
        'Additional cash borrowing increases utilisation and reduces covenant availability dollar for dollar. Letters of credit and the borrowing base otherwise remain unchanged. The supplied new_debt_cash_rate is the full cash cost of additional borrowing for the whole planning period. It replaces the disclosed rate grid only for these scenarios. Existing cash interest is already included in planning_cases. Scheduled principal repays debt outside this ABL and does not restore ABL drawing capacity.',
        'Each planning case covers one simultaneous pro forma twelve-month test period. Use its EBITDA before exceptional items, net capital expenditure paid in cash, scheduled principal, existing cash interest, cash tax and ordinary dividends on the disclosed covenant basis. No IFRS-to-covenant adjustment is required. Working-capital outflow is an additional cash use outside those amounts.',
        'Opening usable cash above the required operating cash floor is zero. EBITDA is cash generated before the listed cash uses and working-capital outflow. There are no other cash flows. Ending cash must remain at or above that floor. A special dividend is paid in cash in the same test period and is a dividend for covenant purposes.',
        'Borrowing and cash equity are nonnegative continuous amounts. Cash equity has no fees, interest or effect on EBITDA, fixed charges or the borrowing base. It is available solely in equity_support. No intra-period liquidity path or covenant cure by increasing EBITDA is modeled.',
        'An upper or lower limit is the sharp supremum or infimum over the allowed funding choices. attainable is 1 only if a feasible choice reaches the exact limit and 0 otherwise. Do not round a strict covenant trigger into an inclusive exemption.'
      ],
      'definitions':{
        'proposal_tests':'One row for every planning_cases scenario and proposals proposal. required_draw is the smallest nonnegative additional borrowing that funds the proposal and all listed cash uses, before applying facility and covenant restrictions. Report the resulting covenant_availability and fixed_charge_ratio even if that proposed borrowing is not permitted. covenant_tested is 1 when the disclosed test applies. feasible is 1 only if this funding choice satisfies the commitment, applicable covenant and ending cash requirements. No new equity.',
        'distribution_frontier':'One row per planning scenario. upper_limit is the sharp upper limit on the nonnegative special cash dividend with no new equity, subject to the stated funding constraints. attainable is the defined indicator. Do not report an arbitrary near-limit amount.',
        'equity_support':'One row for every planning scenario and equity_targets target. lower_limit is the sharp lower limit on nonnegative new cash equity sufficient to fund that target special dividend while satisfying all constraints, with additional borrowing chosen freely. attainable is the defined indicator.'
      },
      'tables':{
        'proposal_tests':table([('scenario','text'),('proposal','text'),('required_draw_usd_million','money'),('covenant_availability_usd_million','money'),('fixed_charge_ratio','ratio'),('covenant_tested','flag'),('feasible','flag')],['scenario','proposal'],support),
        'distribution_frontier':table([('scenario','text'),('upper_limit_usd_million','money'),('attainable','flag')],['scenario'],support),
        'equity_support':table([('scenario','text'),('target','text'),('lower_limit_usd_million','money'),('attainable','flag')],['scenario','target'],support)
      },
      'claims':{
        'claim_1':{'assertion':'Suppressed availability can be added to the committed facility amount as cash borrowing capacity without a commitment increase.','verdict':'contradicted','evidence':[['a01:s01','a01:s04'],['a01:s03','a01:s04']]},
        'claim_2':{'assertion':'Under case_a, a USD 800 million special dividend can be funded without new equity despite a fixed-charge ratio below one at the required draw.','verdict':'supported','evidence':support},
        'claim_3':{'assertion':'Currency translation alone explains the difference between reported covenant availability and commitment less utilisation.','verdict':'unresolved','evidence':[['a01:s01','a01:s02'],['a01:s03']]}
      }
    }


def controls(data):
    result=[]
    def changed(name,reason,edit):
        d=copy.deepcopy(data)
        edit(d)
        result.append((name,reason,d))
    changed('commitment_before_trigger','The committed ceiling can bind while the covenant remains inapplicable.',
            lambda d:d['facility'][0].update(commitment=4351))
    changed('threshold_at_commitment','Equality activates the covenant even at the final committed dollar.',
            lambda d:d['facility'][0].update(covenant_availability=3874))
    changed('interest_cost','Borrowing cost affects both funding and the fixed-charge denominator.',
            lambda d:[s.update(new_debt_cash_rate=.12) for s in d['planning_cases']])
    changed('working_capital','Cash absorption changes funding without changing covenant EBITDA.',
            lambda d:[s.update(working_capital_outflow=s['working_capital_outflow']+150) for s in d['planning_cases']])
    changed('earnings','Covenant headroom and cash generation move together when earnings change.',
            lambda d:[s.update(ebitda=s['ebitda']+175) for s in d['planning_cases']])
    changed('suppressed_and_lc_context','Suppressed availability is not commitment. LC is already included in utilisation.',
            lambda d:d['facility'][0].update(suppressed_availability=7194,letters_of_credit=17))
    def scale(d):
        for row in d['facility']:
            for k in row: row[k]*=2
        for row in d['planning_cases']:
            for k in row:
                if k not in ('scenario','new_debt_cash_rate'): row[k]*=2
        for name in ('proposals','equity_targets'):
            for row in d[name]: row['special_dividend']*=2
    changed('monetary_scale','Double monetary amounts while preserving ratios, decisions and endpoint closure.',scale)
    changed('row_order','Row order carries no financial meaning.',lambda d:[r.reverse() for r in d.values()])
    return result


def mistakes():
    def mutation(table,old,new,reason):
        assert old in SQL[table]
        return {'table':table,'sql':SQL[table].replace(old,new),'rationale':reason}
    return {
      'always_test_covenant':mutation('proposal_tests','(draw<trigger_draw OR ratio>=1)','ratio>=1','Rejects permitted distributions while the test is inapplicable.'),
      'never_test_covenant':mutation('proposal_tests','(draw<trigger_draw OR ratio>=1)','1=1','Treats the initial exemption as permanent after new borrowing.'),
      'ignore_incremental_interest':mutation('proposal_tests','new_debt_cash_rate r','0.0 r','New borrowing finances interest as well as the proposed distribution.'),
      'suppressed_as_commitment':mutation('distribution_frontier','f.commitment-f.utilised_including_lc capacity','f.commitment+f.suppressed_availability-f.utilised_including_lc capacity','Collateral headroom does not increase lender commitments.'),
      'subtract_lc_twice':mutation('distribution_frontier','f.commitment-f.utilised_including_lc capacity','f.commitment-f.utilised_including_lc-f.letters_of_credit capacity','The disclosed utilisation already includes letters of credit.'),
      'always_attainable':mutation('distribution_frontier','MAX(o.attained) attainable','1 attainable','A strict exemption boundary need not permit the limiting distribution.'),
      'equity_as_ebitda_cure':mutation('equity_support','MIN(capacity,(h-special_dividend)/r) active_draw','capacity active_draw','Cash equity does not remove an active fixed-charge constraint.')
    }
