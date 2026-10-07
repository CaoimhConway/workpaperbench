"""Independent financial invariants for the three source-backed evaluation dossiers."""
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'datasets/challenge-v1/authoring'
D = lambda value: Decimal(str(value))


def definition(key):
    return json.loads((ROOT / key / 'definition.json').read_text())


def close_gold(task, values, control=None):
    expected = control['expected'] if control else {
        key: claim['value'] for key, claim in task['gold']['answers'].items()
    }
    for key, value in values.items():
        assert abs(value - D(expected[key])) <= D(task['gold']['answers'][key]['tolerance'])


def test_nvidia_original_and_control_bridges():
    task = definition('a02')
    assert next(r[4] for r in task['tables']['financials']['rows']
                if r[:4] == ['2024-10-27', 9, 'Revenue', 'GAAP']) == 91166
    for control in [None, *task['controls']]:
        tables = task['tables'] if control is None else control['tables']
        f = {(r[0], r[1], r[2], r[3]): D(r[4]) for r in tables['financials']['rows']}
        gross = f[('2024-10-27', 3, 'Gross profit', 'GAAP')]
        gross += sum(D(r[4]) for r in tables['adjustments']['rows']
                     if r[:3] == ['2024-10-27', 3, 'Gross profit'])
        revenue = f[('2024-10-27', 3, 'Revenue', 'GAAP')]
        guidance = {(r[2], r[3]): r for r in tables['guidance']['rows']}
        rg, mg = guidance[('Revenue', 'GAAP')], guidance[('Gross margin', 'non-GAAP')]
        close_gold(task, {'revenue_gap': revenue - D(rg[4]) * (1 + D(rg[5]) / 100),
                          'adjusted_gross_profit': gross, 'adjusted_gross_margin': 100 * gross / revenue,
                          'margin_gap': 10000 * gross / revenue - 100 * D(mg[4]) - D(mg[5])}, control)
        if control is None:
            assert gross == D(26322)
            assert gross == f[('2024-10-27', 3, 'Gross profit', 'non-GAAP')]
        if control and control['name'] == 'compatible_monetary_scale':
            assert gross == D(52644)
        if control and control['name'] == 'signed_component_gap':
            assert gross == f[('2024-10-27', 3, 'Gross profit', 'non-GAAP')] + 25


def test_microsoft_income_identity_and_period_reconciliation():
    task = definition('a03')
    for control in [None, *task['controls']]:
        tables = task['tables'] if control is None else control['tables']
        f = {(r[0], r[1], r[2]): D(r[3]) for r in tables['financials']['rows']}
        for date in ['2024-12-31', '2023-12-31']:
            for months in [3, 6]:
                v = lambda measure: f[(date, months, measure)]
                assert v('Total revenue') == v('Revenue - Product') + v('Revenue - Service and other')
                assert v('Total cost of revenue') == v('Cost of revenue - Product') + v('Cost of revenue - Service and other')
                assert v('Gross margin') == v('Total revenue') - v('Total cost of revenue')
                assert v('Operating income') == v('Gross margin') - v('Research and development') - v('Sales and marketing') - v('General and administrative')
                assert v('Net income') == v('Income before income taxes') - v('Provision for income taxes')
        revenue = f[('2024-12-31', 6, 'Total revenue')] - f[('2024-12-31', 3, 'Total revenue')]
        income = f[('2024-12-31', 6, 'Operating income')] - f[('2024-12-31', 3, 'Operating income')]
        growth = next(r for r in tables['growth']['rows'] if r[0] == 'Azure and other cloud services')
        assert growth[1] + growth[2] == growth[3]
        close_gold(task, {'q1_revenue': revenue, 'q1_operating_income': income,
                          'margin_change': 10000 * (f[('2024-12-31', 3, 'Operating income')] / f[('2024-12-31', 3, 'Total revenue')] - income / revenue),
                          'azure_gap': D(growth[3]) - D(tables['guidance']['rows'][0][5])}, control)
        if control is None:
            assert revenue == D(65585)
            assert income == D(30552)


def test_oracle_after_tax_sign_and_expected_currency_target():
    task = definition('a04')
    for control in [None, *task['controls']]:
        tables = task['tables'] if control is None else control['tables']
        f = {r[2]: D(r[3]) for r in tables['financials']['rows'] if r[:2] == ['2024-11-30', 3]}
        expense = sum(D(r[4]) for r in tables['adjustments']['rows'] if r[:3] == ['2024-11-30', 3, 'Operating expense'])
        tax = sum(D(r[4]) for r in tables['adjustments']['rows'] if r[:3] == ['2024-11-30', 3, 'Income tax expense'])
        upper = D(tables['guidance']['rows'][0][5]) + sum(D(r[2]) for r in tables['guidance_adjustments']['rows'])
        net = f['Net income'] + expense - tax
        close_gold(task, {'guidance_upper': upper, 'eps_gap': f['Non-GAAP diluted EPS'] - upper,
                          'net_income_adjustment': expense - tax, 'adjusted_net_income': net,
                          'adjusted_net_margin': 100 * net / f['Total revenues']}, control)
        if control is None:
            assert (expense, tax, net, upper) == (D(1876), D(820), D(4207), D('1.48'))
            assert f['Non-GAAP net income'] == net
