# Saved final-a03-inexpensive-1 workpaper

Task: `challenge-v1-a03`. [Frozen source dossier](../../../../datasets/challenge-v1/tasks/a03/environment/sources.md).

| Claim | Availability | Value | Unit | Supporting sections |
|---|---|---:|---|---|
| q1_revenue | answered | 69632.0 | usd_million | a03:s02 |
| q1_operating_income | answered | 31653.0 | usd_million | a03:s02 |
| margin_change | answered | 112.6274 | basis_points | a03:s02, a03:s03 |
| azure_gap | answered | -1.0 | percentage_points | a03:s01, a03:s04 |

Shared context: none

Original-dossier proposition verdict: **contradicted**. Supporting sections: a03:s01, a03:s04.

## q1_revenue

```sql
SELECT amount FROM financials WHERE period_end='2024-12-31' AND months=3 AND measure='Total revenue'
```

## q1_operating_income

```sql
SELECT amount FROM financials WHERE period_end='2024-12-31' AND months=3 AND measure='Operating income'
```

## margin_change

```sql
SELECT (h1_oi - q1_oi) * 1.0 / (h1_rev - q1_rev) * 10000 - q1_oi * 1.0 / q1_rev * 10000 FROM (SELECT q1.amount AS q1_rev FROM financials q1 WHERE q1.period_end='2024-12-31' AND q1.months=3 AND q1.measure='Total revenue') q, (SELECT q2.amount AS q1_oi FROM financials q2 WHERE q2.period_end='2024-12-31' AND q2.months=3 AND q2.measure='Operating income') o, (SELECT h1.amount AS h1_rev FROM financials h1 WHERE h1.period_end='2024-12-31' AND h1.months=6 AND h1.measure='Total revenue') h2, (SELECT h2.amount AS h1_oi FROM financials h2 WHERE h2.period_end='2024-12-31' AND h2.months=6 AND h2.measure='Operating income') h3
```

## azure_gap

```sql
SELECT g.constant_currency_percent - gui.high FROM growth g, guidance gui WHERE g.business='Azure and other cloud services' AND gui.business='Azure and other cloud services' AND gui.fiscal_period='Q2FY2025' AND gui.basis='constant_currency'
```
