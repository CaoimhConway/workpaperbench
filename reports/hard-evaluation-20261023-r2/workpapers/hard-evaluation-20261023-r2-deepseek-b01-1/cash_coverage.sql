WITH acq AS (
  SELECT
    year,
    SUM(cash_shares + cash_awards - cash_acquired - unvested_award_charge) AS identified_noncomp,
    SUM(unvested_award_charge) AS deal_comp,
    SUM(required_disposal) AS required_disposal
  FROM acquisitions
  GROUP BY year
),
p AS (
  SELECT
    periods.*,
    COALESCE(acq.identified_noncomp, 0) AS identified_noncomp,
    COALESCE(acq.deal_comp, 0) AS deal_comp,
    COALESCE(acq.required_disposal, 0) AS required_disposal
  FROM periods
  LEFT JOIN acq USING (year)
)
SELECT
  year,
  operating_cash + deal_comp AS operating_cash_before_deal_compensation_usd_million,
  identified_noncomp AS identified_noncompensation_cash_usd_million,
  acquisition_payments - identified_noncomp AS other_acquisition_cash_usd_million,
  divestiture_proceeds - required_disposal AS other_divestiture_cash_usd_million,
  operating_cash - capex - acquisition_payments + divestiture_proceeds AS cash_after_portfolio_investment_usd_million
FROM p
ORDER BY year;
