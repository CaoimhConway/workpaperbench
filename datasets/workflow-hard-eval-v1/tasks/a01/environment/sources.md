# Source dossier

August 27, 2025 Form 8-K and Fifth Amended and Restated Asset-Based Revolving Credit Agreement

https://www.sec.gov/Archives/edgar/data/1646972/000095010325010782/dp233510_ex1001.htm

Source date 2025-08-27. SEC filing index gives August 27, 2025. Intraday time is not used. Contractual amounts and percentages are used as written. Collateral and purchase amounts are authored inputs.

## a01:s01

Form 8-K, Item 1.01, Structure and Borrowing Base

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1646972/000095010325010782/dp233510_8k.htm

The facility has USD 4,000 million revolving commitments, including USD 1,500 million letters of credit and USD 250 million swingline capacity. Credit availability uses the smaller of commitment and borrowing base.

## a01:s02

Exhibit 10.1, section 1.01, definitions Appraised Value and Borrowing Base

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1646972/000095010325010782/dp233510_ex1001.htm

Receivable advance rates are 90%. Script liquidation value advances at 85%. Regular and perishable inventory advances use cost times appraised liquidation-value percentage times 90%, rising to 92.5% for the three four-week periods ending nearest February, March and April. Deduct availability and maturing-debt reserves.

## a01:s03

Exhibit 10.1, section 1.01, Borrowing Base clauses (c)-(f), definitions Perishables Cap and Pharmacy Inventory Cap

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1646972/000095010325010782/dp233510_ex1001.htm

Scripts and pharmacy inventory share a cap: USD 1,000 million or 25% of borrowing base computed without the perishables cap, whichever is smaller. Perishables are capped at 25% of borrowing base computed without that shared cap. Pharmacy inventory separately has a USD 400 million or 10% cap.

## a01:s04

Exhibit 10.1, section 1.01, Loan Cap and Excess Availability, section 2.01(a)(i)

authentic_source_facts

https://www.sec.gov/Archives/edgar/data/1646972/000095010325010782/dp233510_ex1001.htm

Loan Cap is the lesser of revolving commitments and borrowing base. Revolving exposure cannot exceed Loan Cap. Excess Availability is positive Loan Cap less revolving exposure.

## a01:s05

Authored collateral_cases, purchase_sizes and period_cases, and explicit funding scope

authored_assumption

This is an instantaneous, hypothetical borrowing-base funding exercise under the August 27, 2025 Albertsons terms. It is not the issuer's observed collateral certificate or a forecast. Amounts are USD million, except decimal rates and fractions. All receivables, scripts and inventory supplied in collateral_cases satisfy the agreement's eligibility conditions. Inventory costs and script values are already net of their specific reserves. pharmacy_receivables is net of its receivables reserves. There is no eligible pharmacy inventory. availability_reserves includes all remaining borrowing-base deductions, including any maturing indebtedness reserve. Use the stated concentration percentages at their contractual maximum. A borrowing-base calculation without a named cap removes only that cap and retains all other applicable definitions. The ordinary and seasonal cases refer to the disclosed regular rate and the three eligible four-week periods, respectively. No interest-rate or elapsed-time calculation is requested. For each scenario, the purchase plan is a continuous nonnegative cash purchase of otherwise eligible regular and perishable inventory, divided by regular_purchase_fraction. Its cost increases those two inventory cost balances immediately. Their appraised-value percentages remain unchanged. Scripts, receivables, reserves, outstanding loans and letters of credit otherwise stay fixed. The purchase and funding close simultaneously. There is no usable opening cash, new equity, supplier credit, disposal, tax, fee or other cash flow. Additional revolving cash borrowing is the only funding source. All other draw conditions and financial covenants are satisfied. No accordion commitment, overadvance, FILO loan or other borrowing is available. The letter-of-credit and swingline subfacilities do not increase aggregate commitment. The maximum purchase is the largest exact purchase cost that can be paid while respecting both aggregate commitment and the post-purchase borrowing base. No minimum excess-availability buffer is imposed in this exercise. All comparisons use unrounded values.

## Normalized input tables

Table origins distinguish source facts from authored scenarios. Full source documents are not redistributed.

### facility_terms

authentic_source_facts

```json
[
  {
    "commitment": 4000,
    "lc_sublimit": 1500,
    "swingline_sublimit": 250,
    "receivable_rate": 0.9,
    "script_rate": 0.85,
    "ordinary_inventory_rate": 0.9,
    "seasonal_inventory_rate": 0.925,
    "shared_dollar_cap": 1000,
    "shared_fraction": 0.25,
    "perishable_fraction": 0.25
  }
]
```

### collateral_cases

authored_assumption

```json
[
  {
    "scenario": "case_a",
    "credit_card_receivables": 250,
    "pharmacy_receivables": 400,
    "script_liquidation_value": 2500,
    "regular_inventory_cost": 2000,
    "regular_appraisal": 0.65,
    "perishable_inventory_cost": 1800,
    "perishable_appraisal": 0.5,
    "availability_reserves": 150,
    "loans": 1800,
    "letters_of_credit": 120,
    "regular_purchase_fraction": 0.6
  },
  {
    "scenario": "case_b",
    "credit_card_receivables": 250,
    "pharmacy_receivables": 400,
    "script_liquidation_value": 700,
    "regular_inventory_cost": 600,
    "regular_appraisal": 0.65,
    "perishable_inventory_cost": 3000,
    "perishable_appraisal": 0.5,
    "availability_reserves": 200,
    "loans": 1100,
    "letters_of_credit": 100,
    "regular_purchase_fraction": 0.2
  },
  {
    "scenario": "case_c",
    "credit_card_receivables": 250,
    "pharmacy_receivables": 400,
    "script_liquidation_value": 3000,
    "regular_inventory_cost": 4500,
    "regular_appraisal": 0.65,
    "perishable_inventory_cost": 600,
    "perishable_appraisal": 0.5,
    "availability_reserves": 150,
    "loans": 3100,
    "letters_of_credit": 200,
    "regular_purchase_fraction": 0.8
  }
]
```

### period_cases

authored_assumption

```json
[
  {
    "period": "ordinary",
    "seasonal": 0
  },
  {
    "period": "seasonal",
    "seasonal": 1
  }
]
```

### purchase_sizes

authored_assumption

```json
[
  {
    "proposal": "plan_1",
    "purchase_cost": 500
  },
  {
    "proposal": "plan_2",
    "purchase_cost": 1200
  },
  {
    "proposal": "plan_3",
    "purchase_cost": 2000
  }
]
```

Only concise attributed factual definitions and normalized contractual observations are redistributed. Full issuer documents remain local and are excluded from the project MIT license. Authored scenarios and annotations are separate.
