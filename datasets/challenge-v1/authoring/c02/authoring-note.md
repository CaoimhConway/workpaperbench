# Private authoring note

The 2024 10-K reports comparative 2023 revenue-category values after reclassification. Annual Trading Volume comes from the shareholder letter and is rounded to whole USD billions. I checked the table rows in the captured primary filings. 2023 and 2024 transaction-revenue-to-volume values are ratios of different scopes: transaction revenue includes derivatives, but Trading Volume is spot-only and excludes third-party venues. The ratio must remain explicitly a proxy and not a fee rate.

Independent Decimal calculations use the displayed thousand-dollar revenue and billion-dollar volume figures. Formula: transaction-revenue proxy percent = 100 × (USD thousand / 1,000,000) / USD billion. Proxy change is 100 times the percentage-point change, in basis points.

Base values: transaction revenue growth 162.30398498605604, spot Trading Volume growth 148.2905982905983, 2024 proxy 0.34303898450946646, 2023 proxy 0.3247123931623931623931623932, proxy change 1.8326591347073276 bps.

Controls alter one scoped economic input with matching totals. The first increases 2024 consumer transaction revenue by USD 150,000 thousand and updates transaction and net revenue totals. The second increases 2023 other transaction revenue by USD 80,000 thousand and updates transaction and net revenue totals. The third increases 2024 consumer spot volume by USD 10 billion and the spot total by the same amount. All controls preserve category totals, units and annual periods. Each calculated claim changes in at least one control.

Wrong approaches include using total revenue instead of total transaction revenue, mixing USD thousand with USD billion without conversion, using Q4 values, treating rounded volume growth as exact, or interpreting the ratio as a realized fee rate despite derivative and venue differences. A candidate-only shortcut is copying the proxy constant because the underlying amounts are in a public source, instead of deriving it from the provided rows and surviving controls.

The requested count of payments between businesses is not present in these source observations. The reported operating metric is rounded USD spot Trading Volume by consumer and institutional type, and its definition describes spot-matched trades rather than a count of business payments. The correct status is insufficient evidence with `no_eligible_observation`, unit `count`, null value and null SQL. Zero would claim an observed count and is not supported. This answer is grounded in c02:s03 and c02:s04 only.
