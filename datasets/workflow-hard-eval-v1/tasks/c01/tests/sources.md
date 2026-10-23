# Source dossier

Constellation Energy receivables financing and nine-month cash flows

https://www.sec.gov/Archives/edgar/data/1868275/000186827525000092/ceg-20250930.htm

Source date 2025-11-07.  Displayed whole USD million throughout. The 2024 and 2025 cash-flow periods both end September 30 and cover nine months. Balance dates are separate. The December 31, 2024 amendment is outside the earlier cash-flow window. Source policy classifications are normalized in facility_policy. No undisclosed customer-collection total or cash-timing advantage is inferred for separate tariff sales.

## c01:s01

CEG Parent Consolidated Statements of Cash Flows, printed p. 6, nine months ended September 30, 2025 and 2024

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1868275/000186827525000092/ceg-20250930.htm

Use the Constellation Energy Corporation consolidated statement. The separately presented Generation LLC statement has different amounts. Collateral received or posted is a signed operating cash-flow item. The DPP supplemental amount is a noncash investing and financing disclosure.

## c01:s02

Note 7, Accounts Receivable, Sales of Customer Accounts Receivable, printed p. 24, prior-facility flow table and footnotes

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1868275/000186827525000092/ceg-20250930.htm

Receivables were sold for cash and a subordinated retained interest called DPP. DPP collections were investing cash flow. The 2024 table shows 1,688 proceeds from new transfers, 7,404 DPP collections and 9,092 cash collections reinvested. Receivables sold were 9,370. The DPP collection figure excludes a 300 net cash payment to reduce purchaser funding. Net DPP investing cash was 7,104.

## c01:s03

Note 7, printed p. 24, December 31, 2024 amendment. Note 12, Accounts Receivable Facility, printed p. 34. MD&A cash flows, printed pp. 63-64

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1868275/000186827525000092/ceg-20250930.htm

The amended facility retains receivables and uses secured revolving loans. Customer collections now enter operating activities and facility draws and repayments enter financing activities. Outstanding DPP was forgiven in exchange for reassigned receivables of 1,529 at December 31, 2024. Facility draws were zero at December 31, 2024 and September 30, 2025.

## c01:s04

Note 7, printed p. 24, Other Sales of Customer Accounts Receivables

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1868275/000186827525000092/ceg-20250930.htm

Separate supplier tariffs require receivables sales to utility companies at nominal discounts. Gross sales were 3,207 and 228 in the nine-month periods of 2025 and 2024. Some receivables subject to these tariffs previously went through the NER facility.

## c01:s05

Q3 2024 Form 10-Q, Note 6, Accounts Receivable, printed p. 24, opening and closing fair-value, funding and DPP table

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1868275/000186827524000069/ceg-20240930.htm

At December 31, 2023, derecognized receivables at fair value were 1,516, purchaser funding was 300 and DPP was 1,216. At September 30, 2024, those amounts were 1,766, zero and 1,766. Changes in purchaser cash funding affect DPP.

## c01:s06

Q3 2024 Form 10-Q, Note 6, printed p. 24, loss-on-sale table and footnote

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1868275/000186827524000069/ceg-20240930.htm

The nine-month loss on sales of receivables was 43, representing discounts limited to credit losses.

## c01:s07

Authored analytical presentation and comparison scope

authored_assumption

authored:workflow-hard-eval-v1/c01

The requested presentation puts customer collections in operating activities and net NER purchaser principal cash in financing activities, for both periods. It changes only the NER facility treatment. Separate tariff sales and other cash flows retain their reported treatment. The additional comparison removes the signed collateral cash-flow item and reports cash after capital expenditures.

## Normalized input tables

Table origins distinguish source facts from authored scenarios. Full source documents are not redistributed.

### cash_flows

authentic_source_facts

```json
[
  {
    "period": "2024-9m",
    "sequence": 1,
    "operating": -1448,
    "investing": 5056,
    "financing": -2180,
    "net_cash_change": 1428,
    "collateral": 1495,
    "capex": 1836,
    "noncash_dpp": 7682,
    "net_dpp_investing": 7104
  },
  {
    "period": "2025-9m",
    "sequence": 2,
    "operating": 3432,
    "investing": -2221,
    "financing": -249,
    "net_cash_change": 962,
    "collateral": -192,
    "capex": 1963,
    "noncash_dpp": 0,
    "net_dpp_investing": 0
  }
]
```

### facility_flows

authentic_source_facts

```json
[
  {
    "period": "2024-9m",
    "receivables_sold": 9370,
    "new_transfer_cash": 1688,
    "dpp_collections": 7404,
    "cash_reinvested": 9092,
    "purchaser_payment": 300
  }
]
```

### facility_policy

authentic_source_facts

```json
[
  {
    "period": "2024-9m",
    "basis": "sale"
  },
  {
    "period": "2025-9m",
    "basis": "secured"
  }
]
```

### facility_balances

authentic_source_facts

```json
[
  {
    "as_of": "2023-12-31",
    "sequence": 1,
    "pool_fair_value": 1516,
    "purchaser_funding": 300,
    "dpp": 1216
  },
  {
    "as_of": "2024-09-30",
    "sequence": 2,
    "pool_fair_value": 1766,
    "purchaser_funding": 0,
    "dpp": 1766
  }
]
```

### transition

authentic_source_facts

```json
[
  {
    "as_of": "2024-12-31",
    "dpp_reassigned": 1529,
    "commitment": 1500,
    "opening_draws": 0,
    "closing_draws": 0
  }
]
```

### other_sales

authentic_source_facts

```json
[
  {
    "period": "2024-9m",
    "gross_receivables_sold": 228
  },
  {
    "period": "2025-9m",
    "gross_receivables_sold": 3207
  }
]
```

### credit_losses

authentic_source_facts

```json
[
  {
    "period": "2024-9m",
    "loss_on_sale": 43
  }
]
```

Attributed financial observations and concise definitions only. Issuer documents are excluded from the project MIT license. Full documents are not redistributed.
