"""Reddit liquidation preferences and conversion-dependent owner proceeds."""
import copy
from decimal import Decimal


def d(value):
    return Decimal(str(value))


def securities(data):
    terms = {r['series']: r for r in data['terms']}
    return [dict(row, **{k: v for k, v in terms[row['series']].items() if k != 'series'},
                 preference=d(row['shares']) * d(terms[row['series']]['issue_price'])
                 * d(terms[row['series']]['preference_multiple']) / 1000000,
                 converted=d(row['shares']) * d(terms[row['series']]['conversion_ratio']) / 1000000)
            for row in data['preferred']]


def branch(data, forced):
    items = securities(data)
    common = sum((d(r['shares']) / 1000000 for r in data['common']), d(0))
    converted = [r for r in items if forced and r['forced_eligible']]
    remaining = [r for r in items if r not in converted]
    return common + sum((r['converted'] for r in converted), d(0)), remaining, converted


def funding_at_price(data, forced, price):
    common, remaining, _ = branch(data, forced)
    return common * price + sum((max(r['preference'], r['converted'] * price)
                                 for r in remaining), d(0))


def allocation(data, value, forced=None):
    """Fill contractual preference ranks, then release preferences in price order."""
    value = d(value)
    if forced is None:
        forced = value > d(data['trigger'][0]['valuation'])
    common, remaining, converted = branch(data, forced)
    amounts = {r['series']: d(0) for r in securities(data)}
    total = sum((r['preference'] for r in remaining), d(0))
    if value <= total:
        available = value
        for rank in sorted({r['rank'] for r in remaining}):
            group = [r for r in remaining if r['rank'] == rank]
            claim = sum((r['preference'] for r in group), d(0))
            funded = min(available, claim)
            for row in group:
                amounts[row['series']] = funded * row['preference'] / claim
            available -= funded
        price = d(0)
    else:
        residual = value - total
        denominator = common
        for row in sorted(remaining, key=lambda r: (r['preference'] / r['converted'], r['series'])):
            if residual / denominator > row['preference'] / row['converted']:
                residual += row['preference']
                denominator += row['converted']
        price = residual / denominator
        amounts.update({r['series']: max(r['preference'], r['converted'] * price) for r in remaining})
    amounts.update({r['series']: r['converted'] * price for r in converted})
    amounts.update({r['security']: d(r['shares']) / 1000000 * price for r in data['common']})
    return amounts, price


def calculate(data):
    threshold = d(data['trigger'][0]['valuation'])
    payouts, frontiers, targets = [], [], []
    counts = {r['series']: d(r['shares']) / 1000000 for r in data['preferred']}
    counts.update({r['security']: d(r['shares']) / 1000000 for r in data['common']})
    for case in data['sale_cases']:
        amounts, _ = allocation(data, case['proceeds'])
        payouts.extend([case['sale_case'], name, float(value), float(value / counts[name])]
                       for name, value in amounts.items())
    for row in securities(data):
        if row['forced_eligible']:
            continue
        price = row['preference'] / row['converted']
        feasible = [funding_at_price(data, forced, price) for forced in [False, True]
                    if (funding_at_price(data, forced, price) > threshold) == forced]
        assert feasible, 'a voluntary frontier must be reached continuously'
        frontiers.append([row['series'], float(min(feasible)), float(price)])
    for target in data['owner_targets']:
        name, desired = target['security'], d(target['cash_target'])
        assert desired > 0
        candidates = []
        for forced in [False, True]:
            _, remaining, converted = branch(data, forced)
            holder = next((r for r in remaining if r['series'] == name), None)
            if holder is not None and desired <= holder['preference']:
                senior = sum((r['preference'] for r in remaining if r['rank'] < holder['rank']), d(0))
                peer = sum((r['preference'] for r in remaining if r['rank'] == holder['rank']), d(0))
                required = senior + desired * peer / holder['preference']
            else:
                quantity = next((r['converted'] for r in remaining + converted if r['series'] == name),
                                counts.get(name))
                required = funding_at_price(data, forced, desired / quantity)
            if not forced and required <= threshold:
                candidates.append((required, 1))
            if forced:
                candidates.append((max(required, threshold), int(required > threshold)))
        minimum = min(value for value, _ in candidates)
        attained = max(flag for value, flag in candidates if value == minimum)
        targets.append([target['target_case'], float(minimum), attained])
    return {'sale_allocations': payouts, 'conversion_frontiers': frontiers, 'owner_funding': targets}


TERMS = """WITH terms_full AS (
 SELECT p.*,t.issue_price,t.preference_multiple,t.conversion_ratio,t.rank,t.forced_eligible,
 p.shares*t.issue_price*t.preference_multiple/1000000.0 preference,
 p.shares*t.conversion_ratio/1000000.0 converted
 FROM preferred p JOIN terms t USING(series)
), common_count AS (SELECT SUM(shares)/1000000.0 shares FROM common)
"""

SALE = TERMS + """, cases AS (
 SELECT s.*,s.proceeds>t.valuation forced FROM sale_cases s CROSS JOIN trigger t
), remaining AS (
 SELECT c.sale_case,c.proceeds,n.* FROM cases c CROSS JOIN terms_full n
 WHERE NOT(c.forced=1 AND n.forced_eligible=1)
), totals AS (
 SELECT c.*,b.shares+COALESCE((SELECT SUM(n.converted) FROM terms_full n
 WHERE c.forced=1 AND n.forced_eligible=1),0) base,
 COALESCE((SELECT SUM(preference) FROM remaining r WHERE r.sale_case=c.sale_case),0) preference_total
 FROM cases c CROSS JOIN common_count b
), prefixes AS (
 SELECT r.*,SUM(preference) OVER(PARTITION BY sale_case ORDER BY preference/converted,series
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) removed,
 SUM(converted) OVER(PARTITION BY sale_case ORDER BY preference/converted,series
 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) added
 FROM remaining r
), prices AS (
 SELECT sale_case,MAX(0.0,MIN(price)) price FROM (
 SELECT sale_case,(proceeds-preference_total)/base price FROM totals
 UNION ALL SELECT p.sale_case,(t.proceeds-t.preference_total+p.removed)/(t.base+p.added)
 FROM prefixes p JOIN totals t USING(sale_case)
 ) GROUP BY sale_case
), payments AS (
 SELECT c.sale_case,n.series security,n.shares,
 CASE WHEN c.forced=1 AND n.forced_eligible=1 THEN n.converted*p.price
 WHEN c.proceeds>=t.preference_total THEN MAX(n.preference,n.converted*p.price)
 ELSE MIN(n.preference,MAX(0.0,c.proceeds-COALESCE((SELECT SUM(r.preference)
 FROM remaining r WHERE r.sale_case=c.sale_case AND r.rank<n.rank),0))*n.preference/
 (SELECT SUM(r.preference) FROM remaining r WHERE r.sale_case=c.sale_case AND r.rank=n.rank)) END cash
 FROM cases c CROSS JOIN terms_full n JOIN prices p USING(sale_case) JOIN totals t USING(sale_case)
 UNION ALL SELECT p.sale_case,c.security,c.shares,c.shares/1000000.0*p.price FROM prices p CROSS JOIN common c
) SELECT sale_case,security,cash cash_usd_million,cash*1000000.0/shares payout_per_share FROM payments"""

BRANCHES = TERMS + """, modes(forced) AS (SELECT 0 UNION ALL SELECT 1), branch_totals AS (
 SELECT m.forced,b.shares+SUM(CASE WHEN m.forced=1 AND t.forced_eligible=1
 THEN t.converted ELSE 0.0 END) base FROM modes m CROSS JOIN common_count b CROSS JOIN terms_full t
 GROUP BY m.forced,b.shares
), remaining AS (
 SELECT m.forced,t.* FROM modes m CROSS JOIN terms_full t WHERE NOT(m.forced=1 AND t.forced_eligible=1)
)
"""

SQL = {
    'sale_allocations': SALE,
    'conversion_frontiers': BRANCHES + """, candidates AS (
 SELECT n.series,b.forced,n.preference/n.converted price,
 b.base*n.preference/n.converted+SUM(MAX(r.preference,r.converted*n.preference/n.converted)) proceeds
 FROM terms_full n CROSS JOIN branch_totals b JOIN remaining r ON r.forced=b.forced
 WHERE n.forced_eligible=0 GROUP BY n.series,b.forced,n.preference,n.converted,b.base
) SELECT c.series,MIN(c.proceeds) proceeds_usd_million,c.price common_payout_per_share
 FROM candidates c CROSS JOIN trigger t WHERE (c.proceeds>t.valuation)=c.forced
 GROUP BY c.series,c.price""",
    'owner_funding': BRANCHES + """, owners AS (
 SELECT series security,converted quantity FROM terms_full
 UNION ALL SELECT security,shares/1000000.0 FROM common
), candidates AS (
 SELECT q.target_case,b.forced,
 CASE WHEN h.series IS NOT NULL AND q.cash_target<=h.preference THEN
 COALESCE((SELECT SUM(r.preference) FROM remaining r WHERE r.forced=b.forced AND r.rank<h.rank),0)
 +q.cash_target/h.preference*(SELECT SUM(r.preference) FROM remaining r WHERE r.forced=b.forced AND r.rank=h.rank)
 ELSE b.base*q.cash_target/o.quantity+(SELECT SUM(MAX(r.preference,r.converted*q.cash_target/o.quantity))
 FROM remaining r WHERE r.forced=b.forced) END required
 FROM owner_targets q JOIN owners o USING(security) CROSS JOIN branch_totals b
 LEFT JOIN remaining h ON h.forced=b.forced AND h.series=q.security
), feasible AS (
 SELECT c.target_case,CASE WHEN forced=1 THEN MAX(required,t.valuation) ELSE required END value,
 CASE WHEN forced=0 OR required>t.valuation THEN 1 ELSE 0 END attained
 FROM candidates c CROSS JOIN trigger t WHERE forced=1 OR required<=t.valuation
), minima AS (SELECT target_case,MIN(value) value FROM feasible GROUP BY target_case)
 SELECT m.target_case,m.value proceeds_infimum_usd_million,MAX(f.attained) attained
 FROM minima m JOIN feasible f ON f.target_case=m.target_case AND f.value=m.value
 GROUP BY m.target_case,m.value""",
}


def alternatives():
    """Exhaust all preference/conversion subsets instead of ordered frontiers."""
    replacement = """numbered AS (
 SELECT r.*,ROW_NUMBER() OVER(PARTITION BY sale_case ORDER BY series)-1 position FROM remaining r
), masks(mask) AS (SELECT 0 UNION ALL SELECT mask+1 FROM masks WHERE mask<511), prices AS (
 SELECT t.sale_case,MAX(0.0,(
 SELECT MIN((t.proceeds-t.preference_total+
 (SELECT COALESCE(SUM(n.preference),0) FROM numbered n
  WHERE n.sale_case=t.sale_case AND (m.mask & (1 << n.position))!=0))/
 (t.base+(SELECT COALESCE(SUM(n.converted),0) FROM numbered n
  WHERE n.sale_case=t.sale_case AND (m.mask & (1 << n.position))!=0)))
 FROM masks m)) price FROM totals t
), """
    start = SALE.index('prefixes AS (')
    end = SALE.index('payments AS (')
    return dict(SQL, sale_allocations=(SALE[:start] + replacement + SALE[end:]).replace('WITH terms_full', 'WITH RECURSIVE terms_full', 1))


def declaration(columns, keys, evidence):
    return {'columns': {name: ({'type': 'text', 'unit': 'label'} if unit == 'label' else
                              {'type': 'real', 'unit': unit, 'tolerance': 1e-8}) for name, unit in columns},
            'keys': keys, 'row_order': 'ignored', 'duplicates': 'Keys must be unique',
            'evidence': evidence, 'context_evidence_allowed': ['b02:s06']}


def specification():
    support = ['b02:s01', 'b02:s02', 'b02:s03', 'b02:s05']
    alternate = ['b02:s01', 'b02:s02', 'b02:s04', 'b02:s05']
    return {
        'source': 'reddit-2023', 'calculate': calculate, 'sql': SQL,
        'title': 'Reddit liquidation proceeds and conversion-dependent ownership',
        'nearest': ['workflow-hard-pilot-v2/b01', 'workflow-v15/b09', 'workflow-v15/c08'],
        'novelty': 'Infer an endogenous common-share payout from a preference waterfall, mandatory and value-dependent conversions. Find owner funding requirements across a discontinuous contractual trigger, including an unattained infimum. Share voting power, reported carrying value and simple fully converted ownership do not determine cash entitlement.',
        'request': 'Assess hypothetical all-cash liquidation offers using Reddit\'s December 31, 2023 issued capital and the supplied pre-IPO rights. Calculate proceeds received by each original security cohort for every offer. Find the total proceeds and common-share payout at each nonmandatory series\' voluntary conversion indifference point. Find the infimum of total proceeds that meets each owner cash target, and determine whether that infimum itself meets the target. These are counterfactual liquidation sensitivities, not the actual IPO or a GAAP EPS calculation.',
        'assumptions': 'Authored scenario: Each offer qualifies as a Liquidation Event with all necessary approvals and no waiver of the supplied economic rights. For these scenarios, company valuation for the contractual trigger equals the net cash proceeds legally distributable to the listed stockholders. Freeze the issued shares and conversion ratios at December 31, 2023, with no other mandatory-conversion event, new dividends, recapitalizations or rate adjustments. Use the charter issue prices and preference multiples at their displayed precision. Reported aggregate preferences and carrying values remain contextual observations. Treat all claims outside the listed issued stock, including unissued equity awards, as settled outside this cash pool with no new shares entering it. No award-settlement amount is inferred. Cash proceeds are nonnegative and divisible, with no cent rounding or taxes. Track cash by original cohort even after conversion. Apply the contractual deemed-conversion provision, with no preferential distribution retained on shares treated as converted. Only cash amounts and numerical frontiers are graded, not arbitrary conversion choices at an indifference tie. All owner targets are positive.',
        'definitions': {
            'sale_allocations': 'One row for each sale_case and original security cohort. Use each preferred series label and the common stock labels common_A and common_B. Cash is USD million received by that entire original cohort, including proceeds after conversion. payout_per_share is USD per original share, not voting power or per newly converted share.',
            'conversion_frontiers': 'One row for each series with forced_eligible=0. proceeds_usd_million is the liquidation consideration at which retaining its preference and receiving common-stock proceeds are economically equal, accounting for all other series. common_payout_per_share is the corresponding USD per common share. Equal conversion alternatives at a tie receive the same cash.',
            'owner_funding': 'One row per target_case. proceeds_infimum_usd_million is the greatest lower bound on nonnegative liquidation proceeds that gives the specified original cohort at least cash_target USD million. attained is 1 if the infimum itself meets the cash target, otherwise 0. A value that becomes feasible only immediately above the boundary is not an attained minimum.'},
        'tables': {
            'sale_allocations': declaration([('sale_case','label'),('security','label'),('cash_usd_million','usd_million'),('payout_per_share','usd_per_share')], ['sale_case','security'], [support,alternate]),
            'conversion_frontiers': declaration([('series','label'),('proceeds_usd_million','usd_million'),('common_payout_per_share','usd_per_share')], ['series'], [support,alternate]),
            'owner_funding': declaration([('target_case','label'),('proceeds_infimum_usd_million','usd_million'),('attained','indicator')], ['target_case'], [support,alternate])},
        'claims': {
            'claim_1': {'assertion': 'Every original security cohort receives at least as much cash in the USD 241 million offer as in the USD 240 million offer.', 'verdict': 'contradicted', 'evidence': [support,alternate,['b02:s01','b02:s04','b02:s05']]},
            'claim_2': {'assertion': 'The Series A-1 cohort receives no cash at the USD 240 million offer but receives positive cash at the USD 2,500 million offer.', 'verdict': 'supported', 'evidence': [support,alternate,['b02:s01','b02:s04','b02:s05']]},
            'claim_3': {'assertion': 'The total contractual cash settlement owed to all unissued equity award holders in an actual liquidation would be zero.', 'verdict': 'unresolved', 'evidence': [['b02:s05','b02:s06'],['b02:s06']]}}
    }


def controls(original):
    result = []
    def add(name, rationale, mutation):
        data = copy.deepcopy(original)
        mutation(data)
        result.append((name, rationale, data))
    add('row_order', 'Reorder all rows without changing their identities or rights.', lambda data: [r.reverse() for r in data.values()])
    def scale(data):
        for table, fields in {'preferred':['shares','reported_preference','carrying'], 'common':['shares'],
                              'sale_cases':['proceeds'], 'owner_targets':['cash_target'], 'trigger':['valuation']}.items():
            for row in data[table]:
                for field in fields:
                    row[field] *= 2
    add('scale', 'Double issued shares and every aggregate cash amount and threshold. Per-share rights and per-share payouts stay fixed.', scale)
    add('carrying_only', 'Change preferred book carrying values alone. Contractual liquidation rights do not change.', lambda data: [r.update(carrying=r['carrying']*0.7) for r in data['preferred']])
    add('trigger_lower', 'Lower only the synthetic contractual mandatory-conversion threshold to USD 120 million.', lambda data: data['trigger'][0].update(valuation=120.0))
    add('trigger_higher', 'Raise the synthetic mandatory threshold above some voluntary conversions. Remaining rights are unchanged.', lambda data: data['trigger'][0].update(valuation=3000.0))
    add('junior_seniority', 'Promote the synthetic A-1 claim to the same liquidation rank as other preferred claims. This changes distressed recoveries, not share counts.', lambda data: next(r for r in data['terms'] if r['series']=='A-1').update(rank=1))
    def right_change(data):
        row = next(r for r in data['terms'] if r['series']=='E')
        row['preference_multiple'] = 1.5
        next(r for r in data['preferred'] if r['series']=='E')['reported_preference'] *= 1.5
    add('preference_right', 'Give synthetic Series E a 1.5-times liquidation preference and adjust its contextual preference observation. Original issue price and conversion ratio stay fixed.', right_change)
    add('conversion_ratio', 'Give synthetic Series E 1.2 common shares per preferred share. Issued preferred shares, issue price, preference and other rights stay fixed.', lambda data: next(r for r in data['terms'] if r['series']=='E').update(conversion_ratio=1.2))
    add('target_shift', 'Replace the Series F target near the discontinuity with USD 55 million, which requires a larger attained funding amount.', lambda data: next(r for r in data['owner_targets'] if r['target_case']=='F_54').update(cash_target=55.0))
    return result


def mistakes():
    return {
        'automatic_at_equality': {'table':'sale_allocations', 'sql':SALE.replace('s.proceeds>t.valuation','s.proceeds>=t.valuation'), 'rationale':'The source trigger is strictly above, not at, USD 240 million.'},
        'ignore_mandatory': {'table':'sale_allocations', 'sql':SALE.replace('s.proceeds>t.valuation','0').replace('CROSS JOIN trigger t',''), 'rationale':'Mandatory conversion can remove a valuable preference even when optional conversion is unfavorable.'},
        'fully_converted': {'table':'sale_allocations', 'sql':TERMS + """SELECT s.sale_case,p.series security,
 s.proceeds*p.converted/(b.shares+(SELECT SUM(converted) FROM terms_full)) cash_usd_million,
 s.proceeds*p.conversion_ratio/(b.shares+(SELECT SUM(converted) FROM terms_full)) payout_per_share
 FROM sale_cases s CROSS JOIN terms_full p CROSS JOIN common_count b
 UNION ALL SELECT s.sale_case,c.security,s.proceeds*c.shares/1000000.0/(b.shares+(SELECT SUM(converted) FROM terms_full)),
 s.proceeds/(b.shares+(SELECT SUM(converted) FROM terms_full)) FROM sale_cases s CROSS JOIN common c CROSS JOIN common_count b""", 'rationale':'Fully converted ownership ignores preference rights and endogenous conversion incentives.'},
        'carrying_as_preference': {'table':'sale_allocations', 'sql':SALE.replace('p.shares*t.issue_price*t.preference_multiple/1000000.0 preference','p.carrying preference'), 'rationale':'The balance-sheet carrying amount is not the contractual liquidation preference.'},
        'all_preferred_pari_passu': {'table':'sale_allocations', 'sql':SALE.replace('t.conversion_ratio,t.rank,t.forced_eligible','t.conversion_ratio,1 rank,t.forced_eligible'), 'rationale':'Series A-1 is junior while it remains preferred.'},
        'double_participation': {'table':'sale_allocations', 'sql':SALE.replace('MAX(n.preference,n.converted*p.price)','n.preference+n.converted*p.price'), 'rationale':'Converted holders surrender preference rather than receiving both preference and residual.'},
        'fixed_common_denominator': {'table':'conversion_frontiers', 'sql':SQL['conversion_frontiers'].replace('MAX(r.preference,r.converted*n.preference/n.converted)','r.preference'), 'rationale':'Other series already converted at a frontier share the residual and have surrendered their preferences.'},
        'all_infima_attained': {'table':'owner_funding', 'sql':SQL['owner_funding'].replace('MAX(f.attained) attained','1 attained'), 'rationale':'A target reached only above a strict mandatory-conversion discontinuity has no attained minimum.'},
        'ignore_conversion_ratio': {'table':'sale_allocations', 'sql':SALE.replace('p.shares*t.conversion_ratio/1000000.0 converted','p.shares/1000000.0 converted'), 'scope':'controls', 'rationale':'Converted common shares need not equal original preferred shares. The changed-ratio control also distinguishes cash per original share from cash per converted share.'},
    }
