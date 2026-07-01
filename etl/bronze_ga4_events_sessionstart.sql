
-- BRONZE__GA4_EVENTS_SESSIONSTART_DAILY_INCREMENTAL
-- Schedule this script to run once per day.

DECLARE lookback_days INT64 DEFAULT 3;
DECLARE run_date DATE DEFAULT CURRENT_DATE(); -- use on manual runs
-- DECLARE run_date DATE DEFAULT IFNULL(@run_date, CURRENT_DATE()); -- use on scheduled runs
DECLARE start_date DATE DEFAULT DATE_SUB(run_date, INTERVAL lookback_days DAY);
DECLARE end_date DATE DEFAULT DATE_SUB(run_date, INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `g-analytics-487213.bronze_us.ga4_events_sessionstart`
PARTITION BY event_date
OPTIONS (require_partition_filter = TRUE) AS
SELECT
  CAST(event_date AS DATE FORMAT 'YYYYMMDD') AS event_date,
  TIMESTAMP_MICROS(event_timestamp) AS event_timestamp,
  event_name,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'event_id' LIMIT 1) AS event_id,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_location' LIMIT 1) AS page_location,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_title' LIMIT 1) AS page_title,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) AS ga_session_number,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'engaged_session_event' LIMIT 1) AS engaged_session_event,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'session_engaged' LIMIT 1) AS session_engaged,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'source' LIMIT 1) AS traffic_source,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'medium' LIMIT 1) AS traffic_medium,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'campaign' LIMIT 1) AS traffic_campaign,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'term' LIMIT 1) AS traffic_term,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'gclid' LIMIT 1) AS gclid,
  user_id,
  user_pseudo_id,
  is_active_user,
  (CASE
    WHEN (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) = 1 THEN "New user"
    WHEN (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) > 1 THEN "Returning user"
    ELSE NULL
    END) AS user_type,
  device.category AS device_category,
  device.operating_system AS device_operating_system,
  geo.country AS country,
  geo.region AS region,
  geo.city AS city,
  event_dimensions.hostname,
  CONCAT('analytics_253977277.events_', event_date) AS source_table
FROM `mistral-analytics.analytics_253977277.events_*`
WHERE FALSE;

-- Rebuild only recent partitions to keep the load idempotent and absorb late arrivals.
DELETE FROM `g-analytics-487213.bronze_us.ga4_events_sessionstart`
WHERE event_date BETWEEN start_date AND end_date;

INSERT INTO `g-analytics-487213.bronze_us.ga4_events_sessionstart` (
  event_date,
  event_timestamp,
  event_name,
  event_id,
  page_location,
  page_title,
  ga_session_id,
  ga_session_number,
  engaged_session_event,
  session_engaged,
  traffic_source,
  traffic_medium,
  traffic_campaign,
  traffic_term,
  gclid,
  user_id,
  user_pseudo_id,
  is_active_user,
  user_type,
  device_category,
  device_operating_system,
  country,
  region,
  city,
  hostname,
  source_table
)
SELECT
  CAST(event_date AS DATE FORMAT 'YYYYMMDD') AS event_date,
  TIMESTAMP_MICROS(event_timestamp) AS event_timestamp,
  event_name,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'event_id' LIMIT 1) AS event_id,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_location' LIMIT 1) AS page_location,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'page_title' LIMIT 1) AS page_title,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_id' LIMIT 1) AS ga_session_id,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) AS ga_session_number,
  (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'engaged_session_event' LIMIT 1) AS engaged_session_event,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'session_engaged' LIMIT 1) AS session_engaged,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'source' LIMIT 1) AS traffic_source,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'medium' LIMIT 1) AS traffic_medium,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'campaign' LIMIT 1) AS traffic_campaign,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'term' LIMIT 1) AS traffic_term,
  (SELECT ep.value.string_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'gclid' LIMIT 1) AS gclid,
  user_id,
  user_pseudo_id,
  is_active_user,
  (CASE
    WHEN (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) = 1 THEN "New user"
    WHEN (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_number' LIMIT 1) > 1 THEN "Returning user"
    ELSE NULL
    END) AS user_type,
  device.category AS device_category,
  device.operating_system AS device_operating_system,
  geo.country AS country,
  geo.region AS region,
  geo.city AS city,
  event_dimensions.hostname,
  CONCAT('analytics_253977277.events_', event_date) AS source_table
FROM `mistral-analytics.analytics_253977277.events_*`
WHERE event_name like 'session_start'
  AND _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', start_date)
                        AND FORMAT_DATE('%Y%m%d', end_date);