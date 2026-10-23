-- Full-period EPS: test all inclusion subsets to obtain maximum dilution.
-- Optional principal uses full shares at every price; mandatory cash uses excess.
WITH RECURSIVE
note_order AS (
    SELECT n.note, n.principal, n.coupon, n.amortization,
           t.conversion_rate, t.principal_settlement,
           ROW_NUMBER() OVER (ORDER BY n.note) AS seq
    FROM notes AS n JOIN contract_terms AS t ON t.note = n.note
),
effects AS (
    SELECT p.price_case, n.seq,
           CASE WHEN n.principal_settlement = 'choice'
                THEN n.principal * n.conversion_rate / 1000.0
                ELSE MAX(n.principal * n.conversion_rate / 1000.0
                         - n.principal / p.price, 0.0) END AS shares,
           CASE WHEN n.principal_settlement = 'choice'
                THEN n.coupon + n.amortization ELSE 0.0 END AS addback
    FROM price_cases AS p CROSS JOIN note_order AS n
),
elections(include_note) AS (VALUES (0), (1)),
portfolios(price_case, income_case, income, basic_shares, award_shares,
           seq, addback, shares) AS (
    SELECT p.price_case, i.income_case, i.income,
           b.basic_shares, b.award_shares, 0, 0.0, 0.0
    FROM price_cases AS p CROSS JOIN income_cases AS i CROSS JOIN eps_basis AS b
    UNION ALL
    SELECT f.price_case, f.income_case, f.income,
           f.basic_shares, f.award_shares, e.seq,
           f.addback + x.include_note * e.addback,
           f.shares + x.include_note * e.shares
    FROM portfolios AS f
    JOIN effects AS e ON e.price_case = f.price_case AND e.seq = f.seq + 1
    CROSS JOIN elections AS x
)
SELECT price_case, income_case, income / basic_shares AS basic_eps,
       MIN((income + addback) / (basic_shares + award_shares + shares)) AS diluted_eps
FROM portfolios
WHERE seq = (SELECT COUNT(*) FROM note_order)
GROUP BY price_case, income_case, income, basic_shares;
