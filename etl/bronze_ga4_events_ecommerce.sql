
-- BRONZE__GA4_EVENTS_ECOMMERCE_DAILY_INCREMENTAL
-- Schedule this script to run once per day.

DECLARE lookback_days INT64 DEFAULT 3;
DECLARE run_date DATE DEFAULT CURRENT_DATE(); -- use on manual runs
-- DECLARE run_date DATE DEFAULT IFNULL(@run_date, CURRENT_DATE()); -- use on scheduled runs
DECLARE start_date DATE DEFAULT DATE_SUB(run_date, INTERVAL lookback_days DAY);
DECLARE end_date DATE DEFAULT DATE_SUB(run_date, INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `g-analytics-487213.bronze_us.ga4_events_ecommerce`
PARTITION BY event_date
OPTIONS (require_partition_filter = TRUE) AS
SELECT
  CAST(event_date AS DATE FORMAT 'YYYYMMDD') AS event_date,
  TIMESTAMP_MICROS(event_timestamp) AS event_timestamp,
  event_name,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'event_id' LIMIT 1) AS event_id,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'client_id_raw' LIMIT 1) AS client_id_raw,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'partner_id' LIMIT 1) AS partner_id,
  (SELECT ep.value.double_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'value' LIMIT 1) AS double_value,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_location' LIMIT 1) AS page_location,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_title' LIMIT 1) AS page_title,
  ecommerce.total_item_quantity AS total_item_quantity,
  ecommerce.purchase_revenue AS purchase_revenue,
  ecommerce.refund_value AS refund_value,
  ecommerce.shipping_value AS shipping_value,
  ecommerce.tax_value AS tax_value,
  ecommerce.transaction_id AS transaction_id,
  items.item_id AS item_id,
  items.item_name AS item_name,
  items.item_brand AS item_brand,
  items.item_variant AS item_variant,
  items.item_category AS item_category,
  items.item_category2 AS item_category2,
  items.item_category3 AS item_category3,
  items.item_category4 AS item_category4,
  items.item_category5 AS item_category5,
  items.price as item_price,
  items.quantity as item_quantity,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) AS ga_session_number,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'source' LIMIT 1) AS traffic_source,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'medium' LIMIT 1) AS traffic_medium,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'campaign' LIMIT 1) AS traffic_campaign,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'term' LIMIT 1) AS traffic_term,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'gclid' LIMIT 1) AS gclid,
  user_id,
  user_pseudo_id,
  is_active_user,
  device.category AS device_category,
  device.operating_system AS device_operating_system,
  geo.country AS country,
  geo.region AS region,
  geo.city AS city,
  event_dimensions.hostname,
  CONCAT('analytics_253977277.events_', event_date) AS source_table
FROM `mistral-analytics.analytics_253977277.events_*`,
UNNEST(items) AS items
WHERE FALSE;

-- Rebuild only recent partitions to keep the load idempotent and absorb late arrivals.
DELETE FROM `g-analytics-487213.bronze_us.ga4_events_ecommerce`
WHERE event_date BETWEEN start_date AND end_date;

INSERT INTO `g-analytics-487213.bronze_us.ga4_events_ecommerce` (
  event_date,
  event_timestamp,
  event_name,
  event_id,
  client_id_raw,
  partner_id,
  double_value,
  page_location,
  page_title,
  total_item_quantity,
  purchase_revenue,
  refund_value,
  shipping_value,
  tax_value,
  transaction_id,
  item_id,
  item_name,
  item_brand,
  item_variant,
  item_category,
  item_category2,
  item_category3,
  item_category4,
  item_category5,
  item_price,
  item_quantity,
  ga_session_id,
  ga_session_number,
  traffic_source,
  traffic_medium,
  traffic_campaign,
  traffic_term,
  gclid,
  user_id,
  user_pseudo_id,
  is_active_user,
  device_category,
  device_operating_system,
  country,
  region,
  city,
  hostname,
  source_table
)
SELECT
  e.event_date,
  e.event_timestamp,
  e.event_name,
  e.event_id,
  e.client_id_raw,
  e.partner_id,
  e.double_value,
  e.page_location,
  e.page_title,
  e.total_item_quantity,
  e.purchase_revenue,
  e.refund_value,
  e.shipping_value,
  e.tax_value,
  e.transaction_id,
  e.item_id,
  e.item_name,
  e.item_brand,
  e.item_variant,
  e.item_category,
  e.item_category2,
  e.item_category3,
  e.item_category4,
  e.item_category5,
  e.item_price,
  e.item_quantity,
  e.ga_session_id,
  e.ga_session_number,
  COALESCE(NULLIF(e.traffic_source, ''), s.traffic_source) AS traffic_source,
  COALESCE(NULLIF(e.traffic_medium, ''), s.traffic_medium) AS traffic_medium,
  COALESCE(NULLIF(e.traffic_campaign, ''), s.traffic_campaign) AS traffic_campaign,
  COALESCE(NULLIF(e.traffic_term, ''), s.traffic_term) AS traffic_term,
  e.gclid,
  e.user_id,
  e.user_pseudo_id,
  e.is_active_user,
  e.device_category,
  e.device_operating_system,
  e.country,
  e.region,
  e.city,
  e.hostname,
  e.source_table
FROM (
  SELECT
    CAST(event_date AS DATE FORMAT 'YYYYMMDD') AS event_date,
    TIMESTAMP_MICROS(event_timestamp) AS event_timestamp,
    event_name,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'event_id' LIMIT 1) AS event_id,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'client_id_raw' LIMIT 1) AS client_id_raw,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'partner_id' LIMIT 1) AS partner_id,
    (SELECT ep.value.double_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'value' LIMIT 1) AS double_value,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_location' LIMIT 1) AS page_location,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_title' LIMIT 1) AS page_title,
    ecommerce.total_item_quantity AS total_item_quantity,
    ecommerce.purchase_revenue AS purchase_revenue,
    ecommerce.refund_value AS refund_value,
    ecommerce.shipping_value AS shipping_value,
    ecommerce.tax_value AS tax_value,
    ecommerce.transaction_id AS transaction_id,
    items.item_id AS item_id,
    items.item_name AS item_name,
    items.item_brand AS item_brand,
    items.item_variant AS item_variant,
    items.item_category AS item_category,
    items.item_category2 AS item_category2,
    items.item_category3 AS item_category3,
    items.item_category4 AS item_category4,
    items.item_category5 AS item_category5,
    items.price as item_price,
    items.quantity as item_quantity,
    (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id,
    (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) AS ga_session_number,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'source' LIMIT 1) AS traffic_source,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'medium' LIMIT 1) AS traffic_medium,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'campaign' LIMIT 1) AS traffic_campaign,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'term' LIMIT 1) AS traffic_term,
    (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'gclid' LIMIT 1) AS gclid,
    user_id,
    user_pseudo_id,
    is_active_user,
    device.category AS device_category,
    device.operating_system AS device_operating_system,
    geo.country AS country,
    geo.region AS region,
    geo.city AS city,
    event_dimensions.hostname,
    CONCAT('analytics_253977277.events_', event_date) AS source_table
  FROM `mistral-analytics.analytics_253977277.events_*`,
  UNNEST(items) AS items
  WHERE event_name IN (
    'view_promotion',
    'view_item_list',
    'view_item',
    'add_to_wishlist',
    'add_to_cart',
    'view_cart',
    'begin_checkout',
    'add_shipping_info',
    'add_payment_info',
    'purchase'
    )
    AND _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', start_date)
                          AND FORMAT_DATE('%Y%m%d', end_date)
) e
LEFT JOIN (
  SELECT user_pseudo_id, ga_session_id,
    MAX(traffic_source) AS traffic_source,
    MAX(traffic_medium) AS traffic_medium,
    MAX(traffic_campaign) AS traffic_campaign,
    MAX(traffic_term) AS traffic_term
  FROM `g-analytics-487213.bronze_us.ga4_events_sessionstart`
  WHERE event_date BETWEEN start_date AND end_date
    AND traffic_medium IS NOT NULL AND traffic_medium != ''
  GROUP BY 1, 2
) s ON e.user_pseudo_id = s.user_pseudo_id
   AND e.ga_session_id  = s.ga_session_id;