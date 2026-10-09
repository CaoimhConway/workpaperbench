WITH p AS (SELECT economic_date,MAX(CASE service WHEN 'Disney+' THEN subscriptions_million END) d,MAX(CASE service WHEN 'Hulu' THEN subscriptions_million END) h
FROM subscriptions WHERE economic_date IN ('2025-06-28','2025-09-27') GROUP BY economic_date)
SELECT c.economic_date,c.d disney_subscriptions_million,c.h hulu_subscriptions_million,c.d+c.h total_service_subscriptions_million,c.d+c.h-p.d-p.h sequential_change_million FROM p c JOIN p ON p.economic_date='2025-06-28'
