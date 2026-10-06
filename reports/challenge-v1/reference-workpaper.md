# Authored Adobe reference workpaper

Task: `challenge-v1-a01`. [Frozen source dossier](../../datasets/challenge-v1/tasks/a01/environment/sources.md).

| Claim | Availability | Value | Unit | Supporting sections |
|---|---|---:|---|---|
| eps_difference | answered | 0.13 | usd_per_share | a01:s01, a01:s04 |
| adjusted_operating_income | answered | 2596.0 | usd_million | a01:s02, a01:s03 |
| adjusted_margin | answered | 46.307527648947556 | percent | a01:s02, a01:s03 |
| margin_bridge | answered | 1139.8501605422762 | basis_points | a01:s02, a01:s03 |

Shared context: none

Original-dossier proposition verdict: **supported**. Supporting sections: a01:s01, a01:s04.

## eps_difference

```sql
SELECT (SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='Non-GAAP diluted net income per share')-(SELECT high FROM guidance WHERE issue_date='2024-09-12' AND period_end='2024-11-29' AND months=3 AND measure='Diluted EPS' AND basis='non-GAAP')
```

## adjusted_operating_income

```sql
WITH x AS (SELECT (SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='GAAP operating income') g,(SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='Total revenue') r,(SELECT SUM(amount) FROM adjustments WHERE period_end='2024-11-29' AND months=3) a) SELECT g+a FROM x
```

## adjusted_margin

```sql
WITH x AS (SELECT (SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='GAAP operating income') g,(SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='Total revenue') r,(SELECT SUM(amount) FROM adjustments WHERE period_end='2024-11-29' AND months=3) a) SELECT 100.0*(g+a)/r FROM x
```

## margin_bridge

```sql
WITH x AS (SELECT (SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='GAAP operating income') g,(SELECT amount FROM financials WHERE period_end='2024-11-29' AND months=3 AND measure='Total revenue') r,(SELECT SUM(amount) FROM adjustments WHERE period_end='2024-11-29' AND months=3) a) SELECT 10000.0*a/r FROM x
```
