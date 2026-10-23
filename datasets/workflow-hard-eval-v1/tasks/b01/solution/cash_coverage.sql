WITH amounts AS (
 SELECT *,cash_shares+cash_awards cash,
 share_consideration+cvr_common+replacement_options+replacement_rsus+cvr_awards noncash
 FROM acquisitions
), deals AS (
 SELECT *,cash-cash_acquired net_cash,
 CASE WHEN method='business_combination' THEN cash+noncash
 ELSE cash-unvested_award_charge+transaction_costs END basis FROM amounts
) SELECT p.year,p.operating_cash+d.unvested_award_charge operating_cash_before_deal_compensation_usd_million,
 d.net_cash-d.unvested_award_charge identified_noncompensation_cash_usd_million,
 p.acquisition_payments-(d.net_cash-d.unvested_award_charge) other_acquisition_cash_usd_million,
 p.divestiture_proceeds-d.required_disposal other_divestiture_cash_usd_million,
 p.operating_cash-p.capex-p.acquisition_payments+p.divestiture_proceeds cash_after_portfolio_investment_usd_million
 FROM periods p JOIN deals d USING(year)
