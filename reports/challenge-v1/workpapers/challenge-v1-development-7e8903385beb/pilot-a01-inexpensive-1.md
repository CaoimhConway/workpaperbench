# Saved pilot-a01-inexpensive-1 workpaper

Task: `challenge-v1-a01`. [Frozen source dossier](../../../../datasets/challenge-v1/tasks/a01/environment/sources.md).

| Claim | Availability | Value | Unit | Supporting sections |
|---|---|---:|---|---|
| eps_difference | answered | 0.13 | usd_per_share | a01:s01, a01:s04 |
| adjusted_operating_income | answered | 2596.0 | usd_million | a01:s03 |
| adjusted_margin | answered | 46.307528 | percent | a01:s02, a01:s03 |
| margin_bridge | answered | 1139.850161 | basis_points | a01:s02, a01:s03 |

Shared context: a01:s01: Q3 FY2024 release - Q4 financial targets guidance (Non-GAAP EPS: $4.63–$4.68 for Q4 FY2024), a01:s02: Q4 FY2024 consolidated statements of income (Total revenue: $5,606M), a01:s03: Q4 FY2024 operating income reconciliation (GAAP: $1,957M, Non-GAAP: $2,596M), a01:s04: Q4 FY2024 diluted earnings reconciliation (Non-GAAP EPS: $4.81)

Original-dossier proposition verdict: **supported**. Supporting sections: a01:s01, a01:s04.

## eps_difference

```sql
SELECT (f.amount - g.high) AS eps_difference FROM financials f JOIN guidance g ON f.period_end = g.period_end AND f.months = g.months AND f.basis = g.basis AND g.issue_date = '2024-09-12' WHERE f.period_end = '2024-11-29' AND f.months = 3 AND f.measure = 'Non-GAAP diluted net income per share' AND f.basis = 'non-GAAP' AND g.period_end = '2024-11-29' AND g.months = 3 AND g.measure = 'Diluted EPS' AND g.basis = 'non-GAAP';
```

## adjusted_operating_income

```sql
SELECT f.amount AS adjusted_operating_income FROM financials f WHERE f.period_end = '2024-11-29' AND f.months = 3 AND f.measure = 'Non-GAAP operating income' AND f.basis = 'non-GAAP';
```

## adjusted_margin

```sql
SELECT (f_oi.amount / f_rev.amount) * 100.0 AS adjusted_margin FROM financials f_oi JOIN financials f_rev ON f_oi.period_end = f_rev.period_end AND f_oi.months = f_rev.months WHERE f_oi.period_end = '2024-11-29' AND f_oi.months = 3 AND f_oi.measure = 'Non-GAAP operating income' AND f_oi.basis = 'non-GAAP' AND f_rev.measure = 'Total revenue' AND f_rev.basis = 'GAAP';
```

## margin_bridge

```sql
SELECT ((f_oi.amount / f_rev.amount) - (f_gai.amount / f_rev.amount)) * 10000.0 AS margin_bridge FROM financials f_oi JOIN financials f_rev ON f_oi.period_end = f_rev.period_end AND f_oi.months = f_rev.months JOIN financials f_gai ON f_oi.period_end = f_gai.period_end AND f_oi.months = f_gai.months WHERE f_oi.period_end = '2024-11-29' AND f_oi.months = 3 AND f_oi.measure = 'Non-GAAP operating income' AND f_oi.basis = 'non-GAAP' AND f_rev.measure = 'Total revenue' AND f_rev.basis = 'GAAP' AND f_gai.measure = 'GAAP operating income' AND f_gai.basis = 'GAAP';
```
