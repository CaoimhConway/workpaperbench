# Saved pilot-a01-reference-1 workpaper

Task: `challenge-v1-a01`. [Frozen source dossier](../../../../datasets/challenge-v1/tasks/a01/environment/sources.md).

| Claim | Availability | Value | Unit | Supporting sections |
|---|---|---:|---|---|
| eps_difference | answered | 0.13 | usd_per_share | a01:s01, a01:s04 |
| adjusted_operating_income | answered | 2596.0 | usd_million | a01:s03 |
| adjusted_margin | answered | 46.307527648947556 | percent | a01:s02, a01:s03 |
| margin_bridge | answered | 1139.8501605422762 | basis_points | a01:s02, a01:s03 |

Shared context: a01:s06

Original-dossier proposition verdict: **supported**. Supporting sections: a01:s01, a01:s04.

## eps_difference

```sql
SELECT (SELECT amount FROM financials WHERE measure = 'Non-GAAP diluted net income per share' AND period_end = '2024-11-29' AND months = 3) - (SELECT high FROM guidance WHERE measure = 'Diluted EPS' AND basis = 'non-GAAP' AND period_end = '2024-11-29' AND months = 3);
```

## adjusted_operating_income

```sql
SELECT (SELECT amount FROM financials WHERE measure = 'GAAP operating income' AND period_end = '2024-11-29' AND months = 3) + (SELECT SUM(amount) FROM adjustments WHERE period_end = '2024-11-29' AND months = 3);
```

## adjusted_margin

```sql
SELECT ((SELECT amount FROM financials WHERE measure = 'GAAP operating income' AND period_end = '2024-11-29' AND months = 3) + (SELECT SUM(amount) FROM adjustments WHERE period_end = '2024-11-29' AND months = 3)) * 100.0 / (SELECT amount FROM financials WHERE measure = 'Total revenue' AND period_end = '2024-11-29' AND months = 3);
```

## margin_bridge

```sql
SELECT (SELECT SUM(amount) FROM adjustments WHERE period_end = '2024-11-29' AND months = 3) * 10000.0 / (SELECT amount FROM financials WHERE measure = 'Total revenue' AND period_end = '2024-11-29' AND months = 3);
```
