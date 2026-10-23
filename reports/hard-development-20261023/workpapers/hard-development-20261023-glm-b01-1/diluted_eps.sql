WITH RECURSIVE
basis AS (
    SELECT basic_shares, award_shares
    FROM eps_basis
),
note_inputs AS (
    SELECT
        n.note,
        n.principal,
        n.coupon,
        n.amortization,
        n.principal * c.conversion_rate / 1000.0 AS full_shares_million
    FROM notes AS n
    JOIN contract_terms AS c ON c.note = n.note
),
candidate_issues AS (
    SELECT
        'award' AS issue,
        p.price_case,
        b.award_shares AS shares,
        0.0 AS numerator_adjustment
    FROM price_cases AS p
    CROSS JOIN basis AS b

    UNION ALL

    SELECT
        'note_2025',
        p.price_case,
        n.full_shares_million,
        n.coupon + n.amortization
    FROM price_cases AS p
    CROSS JOIN note_inputs AS n
    WHERE n.note = '2025'

    UNION ALL

    SELECT
        'note_2027',
        p.price_case,
        n.full_shares_million,
        n.coupon + n.amortization
    FROM price_cases AS p
    CROSS JOIN note_inputs AS n
    WHERE n.note = '2027'

    UNION ALL

    SELECT
        'note_2029',
        p.price_case,
        CASE
            WHEN n.full_shares_million * p.price > n.principal
            THEN n.full_shares_million - n.principal / p.price
            ELSE 0.0
        END,
        0.0
    FROM price_cases AS p
    CROSS JOIN note_inputs AS n
    WHERE n.note = '2029'
),
ranked_issues AS (
    SELECT
        price_case,
        issue,
        shares,
        numerator_adjustment,
        numerator_adjustment / shares AS incremental_eps,
        ROW_NUMBER() OVER (
            PARTITION BY price_case
            ORDER BY numerator_adjustment / shares, issue
        ) AS issue_rank
    FROM candidate_issues
    WHERE shares > 0.0
),
issue_counts AS (
    SELECT price_case, COUNT(*) AS issue_count
    FROM ranked_issues
    GROUP BY price_case
),
eps_iterations AS (
    SELECT
        p.price_case,
        i.income_case,
        i.income,
        0 AS issue_rank,
        i.income AS diluted_numerator,
        b.basic_shares AS diluted_shares
    FROM price_cases AS p
    CROSS JOIN income_cases AS i
    CROSS JOIN basis AS b

    UNION ALL

    SELECT
        e.price_case,
        e.income_case,
        e.income,
        r.issue_rank,
        e.diluted_numerator
            + CASE
                WHEN r.incremental_eps < e.diluted_numerator / e.diluted_shares
                THEN r.numerator_adjustment
                ELSE 0.0
              END,
        e.diluted_shares
            + CASE
                WHEN r.incremental_eps < e.diluted_numerator / e.diluted_shares
                THEN r.shares
                ELSE 0.0
              END
    FROM eps_iterations AS e
    JOIN ranked_issues AS r
      ON r.price_case = e.price_case
     AND r.issue_rank = e.issue_rank + 1
)
SELECT
    e.price_case,
    e.income_case,
    e.income / b.basic_shares AS basic_eps,
    e.diluted_numerator / e.diluted_shares AS diluted_eps
FROM eps_iterations AS e
JOIN issue_counts AS c ON c.price_case = e.price_case
CROSS JOIN basis AS b
WHERE e.issue_rank = c.issue_count
ORDER BY e.price_case, e.income_case;
