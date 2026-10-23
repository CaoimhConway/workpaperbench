WITH amounts AS (
 SELECT *,cash_shares+cash_awards cash,
 share_consideration+cvr_common+replacement_options+replacement_rsus+cvr_awards noncash
 FROM acquisitions
), deals AS (
 SELECT *,cash-cash_acquired net_cash,
 CASE WHEN method='business_combination' THEN cash+noncash
 ELSE cash-unvested_award_charge+transaction_costs END basis FROM amounts
) , bridge AS (
 SELECT p.*,d.unvested_award_charge compensation,d.net_cash,d.required_disposal,
 p.acquisition_payments-d.net_cash+d.unvested_award_charge other_acquisitions,
 p.divestiture_proceeds-d.required_disposal other_disposals
 FROM periods p JOIN deals d USING(year)
) SELECT year,operating_cash+compensation operating_cash_before_deal_compensation_usd_million,
 net_cash-compensation identified_noncompensation_cash_usd_million,
 other_acquisitions other_acquisition_cash_usd_million,other_disposals other_divestiture_cash_usd_million,
 operating_cash+compensation-capex-net_cash-other_acquisitions+required_disposal+other_disposals
 cash_after_portfolio_investment_usd_million FROM bridge
