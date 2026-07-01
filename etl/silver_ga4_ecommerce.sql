-- SILVER__GA4_ECOMMERCE_DAILY_INCREMENTAL
-- Schedule this script to run once per day, after bronze_ga4_events_ecommerce.
-- Aggregates purchase events by channel, campaign, date.
-- Revenue is deduplicated by transaction_id to avoid inflation from UNNEST(items).

DECLARE lookback_days INT64 DEFAULT 3;
DECLARE run_date DATE DEFAULT CURRENT_DATE(); -- use on manual runs
-- DECLARE run_date DATE DEFAULT IFNULL(@run_date, CURRENT_DATE()); -- use on scheduled runs
DECLARE start_date DATE DEFAULT DATE_SUB(run_date, INTERVAL lookback_days DAY);
DECLARE end_date DATE DEFAULT DATE_SUB(run_date, INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `g-analytics-487213.silver_us.ga4_ecommerce`
  PARTITION BY event_date
  OPTIONS (require_partition_filter = TRUE)
AS
SELECT
  event_date,
  traffic_source,
  traffic_medium,
  traffic_campaign,
  traffic_term,
  device_category,
  device_operating_system,
  country,
  region,
  city,
  CAST(0 AS INT64) AS transactions,
  CAST(0 AS INT64) AS total_items,
  CAST(0 AS FLOAT64) AS revenue,
  CAST(0 AS FLOAT64) AS shipping_value,
  CAST(0 AS FLOAT64) AS tax_value,
  CAST(0 AS FLOAT64) AS refund_value,
  CAST(0 AS INT64) AS purchasers
FROM `g-analytics-487213.bronze_us.ga4_events_ecommerce`
WHERE FALSE
GROUP BY ALL;

-- Rebuild only recent partitions to keep the load idempotent and absorb late arrivals.
DELETE FROM `g-analytics-487213.silver_us.ga4_ecommerce`
WHERE event_date BETWEEN start_date AND end_date;

INSERT INTO `g-analytics-487213.silver_us.ga4_ecommerce`
  (event_date,
   traffic_source, traffic_medium, traffic_campaign, traffic_term,
   device_category, device_operating_system,
   country, region, city,
   transactions, total_items, revenue,
   shipping_value, tax_value, refund_value,
   purchasers)
SELECT
  event_date,
  traffic_source,
  traffic_medium,
  traffic_campaign,
  traffic_term,
  device_category,
  device_operating_system,
  country,
  region,
  city,
  COUNT(DISTINCT transaction_id) AS transactions,
  SUM(item_quantity) AS total_items,
  SUM(txn_revenue) AS revenue,
  SUM(txn_shipping) AS shipping_value,
  SUM(txn_tax) AS tax_value,
  SUM(txn_refund) AS refund_value,
  COUNT(DISTINCT user_pseudo_id) AS purchasers
FROM (
  SELECT
    event_date,
    traffic_source,
    traffic_medium,
    traffic_campaign,
    traffic_term,
    device_category,
    device_operating_system,
    country,
    region,
    city,
    user_pseudo_id,
    transaction_id,
    SUM(COALESCE(item_quantity, 0)) AS item_quantity,
    MAX(COALESCE(purchase_revenue, 0)) AS txn_revenue,
    MAX(COALESCE(shipping_value, 0)) AS txn_shipping,
    MAX(COALESCE(tax_value, 0)) AS txn_tax,
    MAX(COALESCE(refund_value, 0)) AS txn_refund
  FROM `g-analytics-487213.bronze_us.ga4_events_ecommerce`
  WHERE event_name = 'purchase'
    AND transaction_id IS NOT NULL
    AND event_date BETWEEN start_date AND end_date
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
)
GROUP BY ALL
ORDER BY event_date DESC, revenue DESC;
