SELECT p.economic_date prior_date,c.economic_date current_date,
c.cash_usd-p.cash_usd cash_change_usd,c.repo_fair_value_usd-p.repo_fair_value_usd repo_change_usd,
c.treasury_fair_value_usd-p.treasury_fair_value_usd treasury_change_usd,
c.reported_assets_usd-p.reported_assets_usd asset_change_usd,c.redeemable_tokens-p.redeemable_tokens token_change,
(c.reported_assets_usd-c.redeemable_tokens)-(p.reported_assets_usd-p.redeemable_tokens) surplus_change_usd
FROM reserve_observations p JOIN reserve_observations c ON
(p.economic_date='2026-01-30' AND c.economic_date='2026-02-10') OR
(p.economic_date='2026-02-10' AND c.economic_date='2026-02-27')
