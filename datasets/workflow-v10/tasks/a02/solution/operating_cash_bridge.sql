WITH p AS (SELECT fiscal_year,months,
SUM(CASE WHEN measure IN ('Depreciation and amortization','Share-based compensation','Deferred income taxes',
'Unrealized (gain) loss on equity investments','Impairment charges for facilities consolidation','Other') THEN amount ELSE 0 END) nc,
SUM(CASE WHEN measure IN ('Accounts receivable','Prepaid expenses and other current assets','Other assets','Accounts payable',
'Accrued expenses and other current liabilities','Other liabilities') THEN amount ELSE 0 END) wc,
MAX(CASE WHEN measure='Net income' THEN amount END) ni,
MAX(CASE WHEN measure='Net cash provided by operating activities' THEN amount END) ocf
FROM cashflows WHERE fiscal_year IN (2024,2025) GROUP BY fiscal_year,months),
periods AS (SELECT * FROM p UNION ALL SELECT a.fiscal_year,9,a.nc-q.nc,a.wc-q.wc,a.ni-q.ni,a.ocf-q.ocf
FROM p a JOIN p q ON a.fiscal_year=q.fiscal_year WHERE a.months=12 AND q.months=3)
SELECT fiscal_year,months,nc noncash_adjustments_usd_million,wc working_capital_change_usd_million,
ni+nc+wc-ocf residual_usd_million FROM periods
