WITH terms AS (
  SELECT * FROM facility_terms
),
base AS (
  SELECT
    c.scenario,
    p.period,
    t.commitment,
    t.receivable_rate * (c.credit_card_receivables + c.pharmacy_receivables) AS receivable_advance,
    t.script_rate * c.script_liquidation_value AS script_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.regular_appraisal * c.regular_inventory_cost AS regular_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.regular_appraisal * c.regular_purchase_fraction AS raw_regular_slope,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.perishable_appraisal * c.perishable_inventory_cost AS perishable_advance,
    CASE WHEN p.seasonal = 1 THEN t.seasonal_inventory_rate ELSE t.ordinary_inventory_rate END
      * c.perishable_appraisal * (1.0 - c.regular_purchase_fraction) AS raw_perishable_slope,
    c.availability_reserves AS reserve,
    c.loans + c.letters_of_credit AS existing_exposure,
    t.shared_dollar_cap,
    t.shared_fraction / (1.0 - t.shared_fraction) AS shared_multiplier,
    t.perishable_fraction / (1.0 - t.perishable_fraction) AS perishable_multiplier
  FROM collateral_cases AS c
  CROSS JOIN period_cases AS p
  CROSS JOIN terms AS t
),
shared_options(shared_branch) AS (
  VALUES ('script'), ('dollar'), ('fraction')
),
perishable_options(perishable_branch) AS (
  VALUES ('raw'), ('fraction')
),
loan_options(loan_branch) AS (
  VALUES ('commitment'), ('base')
),
regimes AS (
  SELECT
    b.*,
    s.shared_branch,
    z.perishable_branch,
    l.loan_branch,
    CASE s.shared_branch
      WHEN 'script' THEN b.script_advance
      WHEN 'dollar' THEN b.shared_dollar_cap
      ELSE b.shared_multiplier * (b.receivable_advance + b.regular_advance
        + b.perishable_advance - b.reserve)
    END AS shared_constant,
    CASE s.shared_branch
      WHEN 'fraction' THEN b.shared_multiplier * (b.raw_regular_slope + b.raw_perishable_slope)
      ELSE 0.0
    END AS shared_branch_slope,
    CASE z.perishable_branch
      WHEN 'raw' THEN b.perishable_advance
      ELSE b.perishable_multiplier * (b.receivable_advance + b.script_advance
        + b.regular_advance - b.reserve)
    END AS perishable_constant,
    CASE z.perishable_branch
      WHEN 'fraction' THEN b.perishable_multiplier * b.raw_regular_slope
      ELSE b.raw_perishable_slope
    END AS perishable_branch_slope
  FROM base AS b
  CROSS JOIN shared_options AS s
  CROSS JOIN perishable_options AS z
  CROSS JOIN loan_options AS l
),
roots AS (
  SELECT
    r.*,
    CASE r.loan_branch
      WHEN 'commitment' THEN r.commitment - r.existing_exposure
      WHEN r.shared_branch_slope + r.raw_regular_slope + r.perishable_branch_slope = 1.0 THEN NULL
      ELSE (r.receivable_advance + r.shared_constant + r.regular_advance
        + r.perishable_constant - r.reserve - r.existing_exposure) / (
        1.0 - r.shared_branch_slope - r.raw_regular_slope - r.perishable_branch_slope
      )
    END AS candidate_purchase
  FROM regimes AS r
  UNION ALL
  SELECT r.*, 0.0 FROM regimes AS r
),
candidates AS (
  SELECT
    r.*,
    CASE r.shared_branch
      WHEN 'script' THEN r.script_advance
      WHEN 'dollar' THEN r.shared_dollar_cap
      ELSE r.shared_multiplier * (
        r.receivable_advance + r.regular_advance + r.raw_regular_slope * r.candidate_purchase
        + r.perishable_advance + r.raw_perishable_slope * r.candidate_purchase - r.reserve
      )
    END AS shared_value,
    CASE r.perishable_branch
      WHEN 'raw' THEN r.perishable_advance + r.raw_perishable_slope * r.candidate_purchase
      ELSE r.perishable_multiplier * (
        r.receivable_advance + r.script_advance + r.regular_advance
        + r.raw_regular_slope * r.candidate_purchase - r.reserve
      )
    END AS perishable_value
  FROM roots AS r
  WHERE r.candidate_purchase >= 0.0
),
validated AS (
  SELECT
    q.*,
    q.receivable_advance + q.shared_value + q.regular_advance
      + q.raw_regular_slope * q.candidate_purchase + q.perishable_value - q.reserve
      AS borrowing_base,
    CASE q.loan_branch
      WHEN 'commitment' THEN q.commitment
      ELSE q.receivable_advance + q.shared_value + q.regular_advance
        + q.raw_regular_slope * q.candidate_purchase + q.perishable_value - q.reserve
    END - q.existing_exposure - q.candidate_purchase AS funding_surplus
  FROM candidates AS q
  WHERE CASE q.shared_branch
      WHEN 'script' THEN q.shared_value <= q.shared_dollar_cap
        AND q.shared_value <= q.shared_multiplier * (
          q.receivable_advance + q.regular_advance + q.raw_regular_slope * q.candidate_purchase
          + q.perishable_advance + q.raw_perishable_slope * q.candidate_purchase - q.reserve
        )
      WHEN 'dollar' THEN q.shared_value <= q.script_advance
        AND q.shared_value <= q.shared_multiplier * (
          q.receivable_advance + q.regular_advance + q.raw_regular_slope * q.candidate_purchase
          + q.perishable_advance + q.raw_perishable_slope * q.candidate_purchase - q.reserve
        )
      ELSE q.shared_value <= q.script_advance AND q.shared_value <= q.shared_dollar_cap
    END
    AND CASE q.perishable_branch
      WHEN 'raw' THEN q.perishable_value <= q.perishable_multiplier * (
        q.receivable_advance + q.script_advance + q.regular_advance
        + q.raw_regular_slope * q.candidate_purchase - q.reserve
      )
      ELSE q.perishable_value <= q.perishable_advance + q.raw_perishable_slope * q.candidate_purchase
    END
    AND CASE q.loan_branch
      WHEN 'commitment' THEN q.commitment <= q.receivable_advance + q.shared_value
        + q.regular_advance + q.raw_regular_slope * q.candidate_purchase + q.perishable_value - q.reserve
      ELSE q.receivable_advance + q.shared_value + q.regular_advance
        + q.raw_regular_slope * q.candidate_purchase + q.perishable_value - q.reserve <= q.commitment
    END
),
ranked AS (
  SELECT
    v.*,
    ROW_NUMBER() OVER (
      PARTITION BY v.scenario, v.period
      ORDER BY v.candidate_purchase DESC, v.shared_branch, v.perishable_branch, v.loan_branch
    ) AS selection_rank
  FROM validated AS v
  WHERE v.funding_surplus >= 0.0
)
SELECT
  scenario,
  period,
  candidate_purchase AS maximum_purchase_usd_million,
  borrowing_base AS borrowing_base_usd_million,
  funding_surplus AS funding_surplus_usd_million
FROM ranked
WHERE selection_rank = 1
ORDER BY scenario, period;
