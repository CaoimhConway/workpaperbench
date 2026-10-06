"""Deterministic task tables from retained Bitcoin and Circle observations."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ROOT / 'datasets/real-v1/captures'


def evidence(identifier, text, origin, period, retrieved, capture_hash, publication=None):
    return {'id': identifier, 'text': text, 'origin': origin, 'period': period,
            'publication': publication, 'retrieved_at': retrieved,
            'capture_sha256': capture_hash,
            'redistribution': 'Attributed public-chain facts or limited issuer factual extracts, not a license to third-party documents'}


def answer(identifier, value, unit, sql, citations):
    return {'id': identifier, 'status': 'answered', 'value': float(value), 'unit': unit,
            'sql': sql, 'evidence': citations, 'reason_code': None}


def definition(identifier, group, tables, changed, instruction, context, records, claims, changed_values, conclusion=None):
    gold = {'answers': {}, 'conclusion': None}
    for claim in claims:
        expected = {'status': claim['status'], 'value': claim['value'], 'unit': claim['unit'],
                    'tolerance': 0.000001, 'evidence': [claim['evidence']]}
        if claim['evidence'] == ['chain:observations', 'chain:definitions']:
            expected['evidence'].append(['chain:observations', 'chain:definitions', 'chain:scope'])
        if claim['evidence'] == ['reserve:observations', 'reserve:definition']:
            expected['evidence'].append(['reserve:observations', 'reserve:definition', 'reserve:timing'])
        if claim['status'] == 'answered':
            expected['changed_value'] = float(changed_values[claim['id']])
        else:
            expected['reason_codes'] = [claim['reason_code']]
        gold['answers'][claim['id']] = expected
    if conclusion:
        gold['conclusion'] = {'verdict': conclusion['verdict'], 'reason_codes': [conclusion['reason_code']], 'evidence': [conclusion['evidence']]}
    if conclusion and conclusion['evidence'] == ['chain:observations', 'chain:definitions']:
        gold['conclusion']['evidence'].append(['chain:observations', 'chain:definitions', 'chain:scope'])
    if conclusion and conclusion['evidence'] == ['reserve:observations', 'reserve:definition']:
        gold['conclusion']['evidence'].append(['reserve:observations', 'reserve:definition', 'reserve:timing'])
    return {'task_id': 'real-v1-' + identifier, 'split': 'evaluation',
            'source_group': group, 'origin': 'deterministic_source_derived', 'previously_exposed': False,
            'tables': tables, 'changed_tables': changed, 'instruction': instruction,
            'context': context, 'evidence': records,
            'reference': {'task_id': 'real-v1-' + identifier, 'answers': claims, 'conclusion': conclusion},
            'gold': gold, 'control_origin': 'deliberately_perturbed_real_data'}


def load_bitcoin():
    directory = CAPTURES / 'bitcoin-halving'
    manifest = json.loads((directory / 'bitcoin-halving.manifest.json').read_text())
    for response in manifest['responses']:
        data = (directory / response['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != response['sha256'] or len(data) != response['bytes']:
            raise ValueError('Bitcoin original source hash mismatch')
    rows, blocks, outputs = [], [], []
    for height in (839999, 840000):
        block = json.loads((directory / f'block-{height}.response').read_bytes())
        page = json.loads((directory / f'transactions-first25-{height}.response').read_bytes())
        if block['height'] != height or len(page) != 25 or block['tx_count'] <= len(page):
            raise ValueError('Unexpected Bitcoin page coverage')
        if len({t['txid'] for t in page}) != 25:
            raise ValueError('Repeated Bitcoin transaction identity')
        subsidy = 5000000000 >> (height // 210000)
        for index, tx in enumerate(page):
            if tx['status'].get('block_hash') != block['id'] or tx['status'].get('block_height') != height or tx['status'].get('confirmed') is not True:
                raise ValueError('Bitcoin transaction/block identity mismatch')
            coinbase = tx['vin'][0].get('is_coinbase') is True
            if coinbase != (index == 0):
                raise ValueError('Bitcoin coinbase page position mismatch')
            output_total = sum(out['value'] for out in tx['vout'])
            if not coinbase:
                recomputed_fee = sum(inp['prevout']['value'] for inp in tx['vin']) - output_total
                if recomputed_fee != tx['fee'] or recomputed_fee < 0:
                    raise ValueError('Bitcoin fee does not reconcile')
            fee = 0 if coinbase else tx['fee']
            rows.append([height, index, tx['txid'], int(coinbase), tx['version'], fee, (tx['weight'] + 3) // 4, output_total])
            for output_index, output in enumerate(tx['vout']):
                outputs.append([height, tx['txid'], index, output_index, output['value']])
        blocks.append([height, block['id'], block['timestamp'], block['tx_count'], 25, subsidy])
    if json.loads((directory / 'block-840000.response').read_bytes())['previousblockhash'] != blocks[0][1]:
        raise ValueError('Bitcoin adjacent block linkage mismatch')
    for total in (sum(r[5] for r in rows), sum(o[4] for o in outputs)):
        if not 0 <= total < 2**63:
            raise ValueError('Bitcoin SQLite sum bound')
    tables = {
        'transactions': {'schema': 'CREATE TABLE transactions(height INTEGER,page_index INTEGER,txid TEXT,is_coinbase INTEGER,version INTEGER,fee_sats INTEGER,vsize INTEGER,output_sats INTEGER)', 'rows': rows},
        'blocks': {'schema': 'CREATE TABLE blocks(height INTEGER,block_hash TEXT,timestamp INTEGER,full_transaction_count INTEGER,captured_transaction_count INTEGER,subsidy_sats INTEGER)', 'rows': blocks},
        'outputs': {'schema': 'CREATE TABLE outputs(height INTEGER,txid TEXT,page_index INTEGER,output_index INTEGER,value_sats INTEGER)', 'rows': outputs},
    }
    changed = copy.deepcopy(tables)
    for row in changed['transactions']['rows']:
        row[5] = row[5] + (row[1] * (1000 if row[0] == 839999 else 10000)) if not row[3] else 0
        row[7] += (row[1] + 1) * 100000
    for row in changed['outputs']['rows']:
        row[4] += (row[2] + 1) * 100000 if row[3] == 0 else 0
    context = '''# Bitcoin capture dictionary
Two Bitcoin Mainnet blocks, 839999 and 840000, selected at the protocol's fourth subsidy halving before values or model outcomes were inspected. Each observed API page contains transaction indices 0 through 24, including the coinbase. This is complete only for that fixed prefix sample. The full blocks contain more transactions. Missing later pages are not zero fees or an instrumentation change.

Values and fees are integer satoshis. One BTC is 100000000 satoshis. Transaction fee is input prevout values minus output values. The virtual size is ceiling(weight / 4), in virtual bytes. A sample aggregate fee rate is sum(noncoinbase fees) / sum(noncoinbase virtual sizes), not the mean of transaction fee-rate scalars. Output amounts include change and cannot be classified as payments here.

version is the transaction's actual consensus serialization version. Matched-version coverage keeps only versions present in both noncoinbase prefix samples, using this same sampling rule. It does not match individual transactions or people and makes no representative-population claim.

The subsidy rule is 5000000000 satoshis right-shifted by floor(height / 210000). Coinbase outputs are claimed compensation, not transaction fees or miner profit. Payout minus the nominal subsidy is called claimed compensation above subsidy. It is not asserted to equal all fees in the block since compensation may be unclaimed. The prefix fees never establish the full-block total.

The captures establish neither business purpose nor account-to-person mappings. A transaction can contain multiple outputs, including change and zero-value outputs. Summed outputs are not payment adoption, unique people or economic growth. The two adjacent blocks cannot establish a causal effect of the halving.

Original observations were retrieved in 2026. Block timestamps are consensus source fields, distinct from retrieval, and do not establish a vendor's historical publication time. Native changed-input controls are explicitly synthetic and alter amounts while preserving schema, sampling and definitions.

Primary API specification: https://github.com/Blockstream/esplora/blob/bb2d9f37bdb0eb0dade45b121a1df3581d7443ea/API.md
Subsidy implementation: https://github.com/bitcoin/bitcoin/blob/v27.0/src/validation.cpp
'''
    provenance = hashlib.sha256((directory / 'bitcoin-halving.manifest.json').read_bytes()).hexdigest()
    retrieval = manifest['retrieved_at_utc']
    records = [
        evidence('chain:observations', 'Observed first-25 transaction pages for blocks 839999 and 840000, with fees, outputs, sizes, versions and block identities.', 'https://blockstream.info/api', 'Bitcoin blocks 839999/840000', retrieval, provenance),
        evidence('chain:definitions', 'Satoshi/BTC units, fees, subsidy, virtual-size aggregation and prefix/matched-version coverage are defined in sources.md.', 'https://github.com/Blockstream/esplora/blob/bb2d9f37bdb0eb0dade45b121a1df3581d7443ea/API.md', 'Bitcoin blocks 839999/840000', retrieval, provenance),
        evidence('chain:scope', 'Only indices 0 through 24 per block are captured. Outputs include change, with no business-purpose or person labels.', 'https://blockstream.info/api', 'Bitcoin blocks 839999/840000', retrieval, provenance),
    ]
    return tables, changed, context, records


def bitcoin_values(tables):
    rows = tables['transactions']['rows']
    block = {r[0]: r for r in tables['blocks']['rows']}
    current = [r for r in rows if r[0] == 840000]
    fees = sum(r[5] for r in current if not r[3])
    payout = sum(r[7] for r in current if r[3])
    versions = {r[4] for r in rows if r[0] == 839999 and not r[3]} & {r[4] for r in current if not r[3]}
    def rate(height, matched=False):
        eligible = [r for r in rows if r[0] == height and not r[3] and (not matched or r[4] in versions)]
        return Decimal(sum(r[5] for r in eligible)) / Decimal(sum(r[6] for r in eligible))
    def growth(matched):
        return (rate(840000, matched) / rate(839999, matched) - 1) * 100
    return {'sample_fees': Decimal(fees) / 100000000,
            'claimed_above_subsidy': Decimal(payout - block[840000][5]) / 100000000,
            'sample_rate_change': growth(False), 'matched_rate_change': growth(True),
            'observed_outputs': Decimal(sum(r[7] for r in current if not r[3])) / 100000000}


def bitcoin_definitions():
    tables, changed, context, records = load_bitcoin()
    values, altered = bitcoin_values(tables), bitcoin_values(changed)
    citations = ['chain:observations', 'chain:definitions']
    fees_sql = "SELECT SUM(fee_sats)/100000000.0 AS value FROM transactions WHERE height=840000 AND is_coinbase=0"
    payout_sql = "SELECT (SUM(output_sats)-(SELECT subsidy_sats FROM blocks WHERE height=840000))/100000000.0 AS value FROM transactions WHERE height=840000 AND is_coinbase=1"
    common_sql = 'SELECT version FROM transactions WHERE is_coinbase=0 GROUP BY version HAVING COUNT(DISTINCT height)=2'
    def rate_sql(matched):
        filter_sql = ' AND version IN (' + common_sql + ')' if matched else ''
        return "WITH rates AS (SELECT height,SUM(fee_sats)*1.0/SUM(vsize) rate FROM transactions WHERE is_coinbase=0" + filter_sql + " GROUP BY height) SELECT 100.0*((SELECT rate FROM rates WHERE height=840000)/(SELECT rate FROM rates WHERE height=839999)-1) AS value"
    result = {}
    result['wp03'] = definition('wp03', 'bitcoin-halving-prefix', tables, changed,
        'For block 840000, report sample_fees in btc for noncoinbase transactions in the captured page, and claimed_above_subsidy in btc for coinbase outputs less the nominal block subsidy. Assess: claimed compensation above subsidy exceeds the fees represented by this noncoinbase prefix sample.',
        context, records,
        [answer('sample_fees', values['sample_fees'], 'btc', fees_sql, citations), answer('claimed_above_subsidy', values['claimed_above_subsidy'], 'btc', payout_sql, citations)], altered,
        {'verdict': 'supported' if values['claimed_above_subsidy'] > values['sample_fees'] else 'contradicted', 'reason_code': 'supported_by_calculation' if values['claimed_above_subsidy'] > values['sample_fees'] else 'contradicted_by_calculation', 'evidence': citations})
    equal = abs(values['sample_rate_change'] - values['matched_rate_change']) <= Decimal('0.000001')
    result['wp06'] = definition('wp06', 'bitcoin-halving-prefix', tables, changed,
        'Compare the noncoinbase prefix samples for blocks 839999 and 840000. Report sample_rate_change in percent for their aggregate fee-per-virtual-byte change. Report matched_rate_change in percent using only transaction versions observed in both samples. Assess: the sample aggregate rate change equals the matched-version rate change.',
        context, records,
        [answer('sample_rate_change', values['sample_rate_change'], 'percent', rate_sql(False), citations), answer('matched_rate_change', values['matched_rate_change'], 'percent', rate_sql(True), citations)], altered,
        {'verdict': 'supported' if equal else 'contradicted', 'reason_code': 'supported_by_calculation' if equal else 'contradicted_by_calculation', 'evidence': citations})
    observable = answer('observed_outputs', values['observed_outputs'], 'btc', "SELECT SUM(output_sats)/100000000.0 AS value FROM transactions WHERE height=840000 AND is_coinbase=0", citations)
    missing = [{'id': name, 'status': 'insufficient_evidence', 'value': None, 'unit': unit, 'sql': None,
                'evidence': ['chain:scope'], 'reason_code': 'missing_required_labels'}
               for name, unit in (('business_payments', 'btc'), ('unique_people', 'count'))]
    result['wp08'] = definition('wp08', 'bitcoin-halving-prefix', tables, changed,
        'For the noncoinbase transactions in the captured block 840000 page, report observed_outputs in btc as the sum of all output values. Also report business_payments in btc and unique_people in count, if identifiable from the supplied evidence. Assess: the observed output total establishes the amount of business payments in this sample.',
        context, records, [observable, *missing], altered,
        {'verdict': 'not_established', 'reason_code': 'missing_required_evidence', 'evidence': ['chain:scope']})
    return result


def circle_definition():
    path = CAPTURES / 'circle-usdc-jan2025.json'
    source = json.loads(path.read_text())
    rows = [[r['report_date'][:10], r['total_supply_usdc'], r['allowed_but_not_issued_usdc'],
             r['access_denied_usdc'], r['circulation_usdc_reported'], r['reserve_fair_value_usd']]
            for r in source['observations']]
    if {row[0] for row in rows} != {'2025-01-06', '2025-01-31'} or len(rows) != 2:
        raise ValueError('Circle report date coverage mismatch')
    if any(row[1] - row[2] - row[3] != row[4] for row in rows):
        raise ValueError('Circle source circulation does not reconcile')

    schema = 'CREATE TABLE reserve_snapshots(report_date TEXT,approved_supply INTEGER,allowed_unissued INTEGER,access_denied INTEGER,circulation INTEGER,reserves_usd INTEGER)'
    tables = {'reserve_snapshots': {'schema': schema, 'rows': rows}}
    changed = copy.deepcopy(tables)
    for index, row in enumerate(changed['reserve_snapshots']['rows']):
        row[1] += (index + 1) * 1000000000
        row[4] = row[1] - row[2] - row[3]
        row[5] += (index + 1) * 1100000000
    def calculate(table):
        by_date = {r[0]: r for r in table['reserve_snapshots']['rows']}
        start, end = by_date['2025-01-06'], by_date['2025-01-31']
        p1, p2 = Decimal(start[1] - start[2] - start[3]), Decimal(end[1] - end[2] - end[3])
        return {'circulating_end': p2 / 1000000, 'circulating_growth': (p2 / p1 - 1) * 100,
                'reserve_headroom': (Decimal(end[5]) - p2) / 1000000}
    values, altered = calculate(tables), calculate(changed)
    original = source['source']
    origin = original['url']
    retrieval = original.get('retrieved_at_utc', original['retrieved_on'])
    capture_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    period = '2025-01-06/2025-01-31 at 23:59 UTC'
    records = [
        evidence('reserve:observations', 'Source-reported approved supply, allowed-but-unissued, access-denied, circulation and reserve fair value snapshots.', origin, period, retrieval, capture_hash),
        evidence('reserve:definition', source['method']['circulation_criteria'] + ' ' + source['method']['reserve_criteria'], origin, period, retrieval, capture_hash),
        evidence('reserve:timing', 'Report dates are January 6 and January 31, 2025 at 23:59 UTC. Independent accountants report and management signature are dated February 27, 2025. Historical first web publication is unknown.', origin, period, retrieval, capture_hash),
    ]
    citations = ['reserve:observations', 'reserve:definition']
    context = '# Circle January 2025 report dictionary\n' + source['method']['circulation_criteria'] + '\n\n' + source['method']['reserve_criteria'] + '\n\n' + source['method']['publication_scope'] + '\n\nThe table contains report dates January 6 and January 31, 2025 at 23:59 UTC. USDC quantities are tokens and reserves are USD fair value. The independent accountants opinion and management signature are dated February 27, 2025. First historical web publication is unknown. Capture retrieval is a separate 2026 date, not contemporaneous availability.\n\nSource: ' + origin + '\n' + '\n\nOne million USDC is 1000000 tokens. USD reserve headroom compares assets with circulation at the report\'s issuer par redemption convention of USD 1 per USDC. This is not a supplied market price, USD market capitalization or period transfer volume. Daily or dated stock observations are not summed to obtain flow. The changed control is synthetic.'
    claims = [
        answer('circulating_end', values['circulating_end'], 'usdc_million', "SELECT (approved_supply-allowed_unissued-access_denied)/1000000.0 AS value FROM reserve_snapshots WHERE report_date='2025-01-31'", citations),
        answer('circulating_growth', values['circulating_growth'], 'percent', "WITH p AS (SELECT report_date,approved_supply-allowed_unissued-access_denied quantity FROM reserve_snapshots) SELECT 100.0*((SELECT quantity FROM p WHERE report_date='2025-01-31')*1.0/(SELECT quantity FROM p WHERE report_date='2025-01-06')-1) AS value", citations),
        answer('reserve_headroom', values['reserve_headroom'], 'usd_million', "SELECT (reserves_usd-(approved_supply-allowed_unissued-access_denied))/1000000.0 AS value FROM reserve_snapshots WHERE report_date='2025-01-31'", citations),
    ]
    return definition('wp04', 'circle-usdc-january-2025', tables, changed,
        'Using Circle\'s January 2025 report, recalculate circulating_end in usdc_million at January 31 from the supply components, circulating_growth in percent from January 6 to January 31, and reserve_headroom in usd_million at January 31 under the issuer par redemption convention. Assess: January 31 reserve fair value covers the defined circulating quantity at that convention.',
        context, records, claims, altered,
        {'verdict': 'supported' if values['reserve_headroom'] >= 0 else 'contradicted', 'reason_code': 'supported_by_calculation' if values['reserve_headroom'] >= 0 else 'contradicted_by_calculation', 'evidence': citations})


def crypto_definitions():
    return {**bitcoin_definitions(), 'wp04': circle_definition()}
