WITH yearly_deal_cash AS (
    SELECT
        year,
        SUM(cash_shares + cash_awards) AS listed_cash_consideration,
        SUM(cash_acquired) AS acquired_cash,
        SUM(unvested_award_charge) AS deal_compensation_cash,
        SUM(required_disposal) AS required_disposal
    FROM acquisitions
    GROUP BY year
),
coverage_components AS (
    SELECT
        p.year,
        p.operating_cash + d.deal_compensation_cash
            AS operating_cash_before_deal_compensation,
        d.listed_cash_consideration
            - d.acquired_cash
            - d.deal_compensation_cash
            AS identified_noncompensation_cash,
        p.acquisition_payments
            - (
                d.listed_cash_consideration
                - d.acquired_cash
                - d.deal_compensation_cash
            ) AS other_acquisition_cash,
        p.divestiture_proceeds - d.required_disposal
            AS other_divestiture_cash,
        p.operating_cash,
        p.capex,
        p.acquisition_payments,
        p.divestiture_proceeds
    FROM periods AS p
    JOIN yearly_deal_cash AS d
        ON d.year = p.year
)
SELECT
    year,
    operating_cash_before_deal_compensation
        AS operating_cash_before_deal_compensation_usd_million,
    identified_noncompensation_cash
        AS identified_noncompensation_cash_usd_million,
    other_acquisition_cash AS other_acquisition_cash_usd_million,
    other_divestiture_cash AS other_divestiture_cash_usd_million,
    operating_cash - capex - acquisition_payments + divestiture_proceeds
        AS cash_after_portfolio_investment_usd_million
FROM coverage_components
ORDER BY year;
