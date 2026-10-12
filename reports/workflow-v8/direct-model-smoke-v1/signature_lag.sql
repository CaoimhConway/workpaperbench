SELECT
  report_date,
  report_signed_date,
  CAST(julianday(report_signed_date) - julianday(report_date) AS INTEGER) AS days_to_signature
FROM reserve_reports;
