WITH deal_cash AS (
    SELECT year,
           SUM(unvested_award_charge) AS compensation_cash,
           SUM(cash_shares + cash_awards - cash_acquired
               - unvested_award_charge) AS noncompensation_cash,
           SUM(required_disposal) AS required_disposal
    FROM acquisitions
    GROUP BY year
)
SELECT p.year,
       p.operating_cash + COALESCE(d.compensation_cash, 0.0)
           AS operating_cash_before_deal_compensation_usd_million,
       COALESCE(d.noncompensation_cash, 0.0)
           AS identified_noncompensation_cash_usd_million,
       p.acquisition_payments - COALESCE(d.noncompensation_cash, 0.0)
           AS other_acquisition_cash_usd_million,
       p.divestiture_proceeds - COALESCE(d.required_disposal, 0.0)
           AS other_divestiture_cash_usd_million,
       p.operating_cash - p.capex - p.acquisition_payments
           + p.divestiture_proceeds AS cash_after_portfolio_investment_usd_million
FROM periods AS p
LEFT JOIN deal_cash AS d ON d.year = p.year
WHERE p.year IN (2019, 2020);
