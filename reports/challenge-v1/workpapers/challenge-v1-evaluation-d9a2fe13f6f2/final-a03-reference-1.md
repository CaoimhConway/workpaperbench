# Saved final-a03-reference-1 workpaper

Task: `challenge-v1-a03`. [Frozen source dossier](../../../../datasets/challenge-v1/tasks/a03/environment/sources.md).

| Claim | Availability | Value | Unit | Supporting sections |
|---|---|---:|---|---|
| q1_revenue | answered | 65585.0 | usd_million | a03:s02, a03:s03 |
| q1_operating_income | answered | 30552.0 | usd_million | a03:s02, a03:s03 |
| margin_change | answered | -112.6274 | basis_points | a03:s02, a03:s03 |
| azure_gap | answered | -1.0 | percentage_points | a03:s01, a03:s04 |

Shared context: none

Original-dossier proposition verdict: **contradicted**. Supporting sections: a03:s01, a03:s04.

## q1_revenue

```sql
SELECT ( (SELECT amount FROM financials WHERE measure='Total revenue' AND months=6 AND period_end='2024-12-31') - (SELECT amount FROM financials WHERE measure='Total revenue' AND months=3 AND period_end='2024-12-31') )
```

## q1_operating_income

```sql
SELECT ( (SELECT amount FROM financials WHERE measure='Operating income' AND months=6 AND period_end='2024-12-31') - (SELECT amount FROM financials WHERE measure='Operating income' AND months=3 AND period_end='2024-12-31') )
```

## margin_change

```sql
SELECT ( ( (SELECT amount FROM financials WHERE measure='Operating income' AND months=3 AND period_end='2024-12-31') / (SELECT amount FROM financials WHERE measure='Total revenue' AND months=3 AND period_end='2024-12-31') ) - ( ( (SELECT amount FROM financials WHERE measure='Operating income' AND months=6 AND period_end='2024-12-31') - (SELECT amount FROM financials WHERE measure='Operating income' AND months=3 AND period_end='2024-12-31') ) / ( (SELECT amount FROM financials WHERE measure='Total revenue' AND months=6 AND period_end='2024-12-31') - (SELECT amount FROM financials WHERE measure='Total revenue' AND months=3 AND period_end='2024-12-31') ) ) ) * 10000
```

## azure_gap

```sql
SELECT ( (SELECT constant_currency_percent FROM growth WHERE business='Azure and other cloud services') - (SELECT high FROM guidance WHERE business='Azure and other cloud services' AND issue_date='2024-10-30') )
```
