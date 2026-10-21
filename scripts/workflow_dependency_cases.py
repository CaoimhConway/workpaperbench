"""Specific financial counterexamples for the independent-operand revision."""
import json

TARGETS = {
    'c01': ('profit_bridge', ['gross_profit_2024_usd_thousand']),
    'b06': ('consumer_activity', ['quarterly_trips_per_monthly_consumer', 'monthly_trips_per_monthly_consumer']),
    'b03': ('spot_revenue_proxy', ['apparent_revenue_to_spot_pct']),
    'c04': ('company_margin_bridge', ['gaap_margin_pct', 'adjusted_margin_pct']),
}
# Bounded comparison cases. These already reject frozen derived values.
AUDIT_TARGETS = {
    'a03': ('operating_margins', ['rldc_margin_pct', 'adjusted_ebitda_margin_pct']),
    'b01': ('reserve_coverage', ['coverage_pct']),
    'b05': ('annual_activity_bridge', ['transaction_revenue_to_tpv_pct']),
    'c03': ('gross_to_net', ['incentive_share_of_gross_pct']),
}


def frozen_columns(sql, spec, columns):
    expressions = []
    for name in spec['columns']:
        if name not in columns:
            expressions.append('"' + name + '"')
            continue
        clauses = []
        for row in spec['rows']:
            values = dict(zip(spec['columns'], row))
            condition = ' AND '.join('"' + key + '"=' + (
                "'" + values[key].replace("'", "''") + "'" if isinstance(values[key], str)
                else str(values[key])) for key in spec['keys'])
            clauses.append('WHEN ' + condition + ' THEN ' + repr(values[name]))
        expressions.append('CASE ' + ' '.join(clauses) + ' END AS "' + name + '"')
    return 'SELECT ' + ','.join(expressions) + ' FROM (\n' + sql.strip().rstrip(';') + '\n)\n'


def artifacts(task, case='reference', audit=False):
    answer = json.loads((task / 'tests/reference.json').read_text())
    gold = json.loads((task / 'tests/gold.json').read_text())
    files = {entry['file']: (task / 'solution' / entry['file']).read_text()
             for entry in answer['tables']}
    key = task.name
    target, columns = (AUDIT_TARGETS if audit else TARGETS)[key]
    name = target + '.sql'
    if case == 'frozen':
        if key == 'c01':
            # Real division reproduces the original observations in both years.
            expression = """CASE WHEN category='Subscription and services-based costs' THEN
 (SELECT r.amount FROM revenues r WHERE r.period_end=costs.period_end
 AND r.months=costs.months AND r.category='Subscription and services-based revenue') *
 CASE period_end WHEN '2023-12-31' THEN 1075129.0/5944842.0
 WHEN '2024-12-31' THEN 1135813.0/7164799.0 END ELSE amount END"""
            anchor = "-amount FROM costs"
            assert files[name].count(anchor) == 1
            files[name] = files[name].replace(anchor, '-(' + expression + ') FROM costs')
        else:
            files[name] = frozen_columns(files[name], gold['tables'][target], columns)
    elif case == 'alternative':
        if key == 'c01':
            files[name] = """WITH pairs AS (
 SELECT c.period_end,
 CASE c.category WHEN 'Transaction-based costs' THEN 'transaction'
 WHEN 'Subscription and services-based costs' THEN 'subscription'
 WHEN 'Hardware costs' THEN 'hardware' WHEN 'Bitcoin costs' THEN 'bitcoin'
 ELSE 'acquired_technology_amortization' END category,
 COALESCE(r.amount,0)-c.amount profit
 FROM costs c LEFT JOIN revenues r ON r.period_end=c.period_end AND r.months=c.months
 AND r.category=replace(c.category,' costs',' revenue')
 WHERE c.months=12 AND c.category!='Total cost of revenue'
 AND c.period_end IN ('2023-12-31','2024-12-31'))
SELECT category,
 SUM(CASE WHEN period_end='2023-12-31' THEN profit ELSE 0 END) gross_profit_2023_usd_thousand,
 SUM(CASE WHEN period_end='2024-12-31' THEN profit ELSE 0 END) gross_profit_2024_usd_thousand,
 SUM(CASE WHEN period_end='2024-12-31' THEN profit ELSE -profit END) change_usd_thousand
 FROM pairs GROUP BY category
"""
        elif key == 'b06':
            files[name] = """SELECT CAST(year AS INTEGER) year,CAST(months AS INTEGER) months,
 trips_million,mapcs_million,
 CAST(trips_million AS REAL)/mapcs_million quarterly_trips_per_monthly_consumer,
 trips_million/(mapcs_million*months*1.0) monthly_trips_per_monthly_consumer
 FROM platform WHERE year>=2024 AND year<=2025 ORDER BY year DESC
"""
        elif key == 'b03':
            files[name] = files[name].replace('100.0*r.amount_usd_million/(1000*s.volume_usd_billion)',
                                             'r.amount_usd_million/(10.0*s.volume_usd_billion)')
        elif key == 'c04':
            for basis in ('gaap', 'adjusted'):
                files[name] = files[name].replace(
                    '100.0*(revenue_usd_million-' + basis + '_expense_usd_million)/revenue_usd_million',
                    '100.0-100.0*' + basis + '_expense_usd_million/revenue_usd_million')
    elif case != 'reference':
        raise ValueError('unknown_dependency_case')
    files['answer.json'] = json.dumps(answer, indent=2) + '\n'
    return {name: value.encode() for name, value in files.items()}


def validate_verdict(verdict, key, case, current=True, audit=False):
    assert verdict['checks']['delivery'] is True
    assert verdict['checks']['financial_answer'] is True
    assert verdict['checks']['numerical_tables'] is True
    assert verdict['checks']['claim_verdicts'] is True
    assert verdict['checks']['evidence'] is True
    assert all(row['original'] for row in verdict['details']['tables'].values())
    if case != 'frozen' or (not current and not audit):
        assert verdict['complete'] is True
        assert verdict['checks']['robustness'] is True
        return
    target = (AUDIT_TARGETS if audit else TARGETS)[key][0]
    assert verdict['complete'] is False
    assert verdict['checks']['robustness'] is False
    failures = []
    for table, row in verdict['details']['tables'].items():
        for control, error in row['control_errors'].items():
            if error:
                assert table == target and error == 'numeric', (table, control, error)
                failures.append(control)
    assert failures
    if not audit:
        from build_workflow_dependency_revision import CONTROLS
        assert failures == [CONTROLS[key]['name']]
