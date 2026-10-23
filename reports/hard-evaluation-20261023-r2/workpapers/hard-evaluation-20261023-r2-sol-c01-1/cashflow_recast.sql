-- USD million; only sale-basis NER cash flows need reclassification.
-- New-transfer cash already enters reported operating cash. Add only
-- DPP customer collections; move the net purchaser principal payment
-- from investing to financing. Noncash DPP is never a cash adjustment.
WITH recast AS (
    SELECT c.period,
           c.operating + CASE WHEN p.basis = 'sale'
               THEN f.dpp_collections ELSE 0 END AS operating_cash,
           c.investing - CASE WHEN p.basis = 'sale'
               THEN c.net_dpp_investing ELSE 0 END AS investing_cash,
           c.financing - CASE WHEN p.basis = 'sale'
               THEN f.purchaser_payment ELSE 0 END AS financing_cash
    FROM cash_flows AS c
    JOIN facility_policy AS p ON p.period = c.period
    LEFT JOIN facility_flows AS f ON f.period = c.period
)
SELECT period, operating_cash, investing_cash, financing_cash,
       operating_cash + investing_cash + financing_cash AS total_cash
FROM recast;
