SELECT DISTINCT report_date,report_signed_date,
CAST(julianday(report_signed_date)-julianday(report_date) AS INTEGER) days_to_signature
FROM reserve_reports WHERE report_date IN ('2025-05-31','2025-06-30')
