
-- BRONZE__GA4_GENERAL_TRAFFIC_DAILY_INCREMENTAL
-- Schedule this script to run once per day.

DECLARE lookback_days INT64 DEFAULT 3;
DECLARE run_date DATE DEFAULT CURRENT_DATE();  -- use on manual runs
-- DECLARE run_date DATE DEFAULT IFNULL(@run_date, CURRENT_DATE()); -- use on scheduled runs
DECLARE start_date DATE DEFAULT DATE_SUB(run_date, INTERVAL lookback_days DAY);
DECLARE end_date DATE DEFAULT DATE_SUB(run_date, INTERVAL 1 DAY);

CREATE TABLE IF NOT EXISTS `g-analytics-487213.silver_us.ga4_general_traffic`
  PARTITION BY event_date
  OPTIONS (require_partition_filter = TRUE)
AS
SELECT
  event_date,
  event_name,
  device_category,
  device_operating_system,
  traffic_source,
  traffic_medium,
  traffic_campaign,
  traffic_term,
  country,
  region,
  city,
  COUNT(DISTINCT CONCAT(ga_session_id, '-', user_pseudo_id)) AS total_sessions,
  COUNT(
    DISTINCT (
      CASE
        WHEN engaged_session_event = 1
          THEN CONCAT(ga_session_id, '-', user_pseudo_id)
        ELSE NULL
        END)) AS engaged_sessions,
  COUNT(DISTINCT user_pseudo_id) AS total_users,
  COUNT(
    DISTINCT (
      CASE WHEN user_type = "New user" THEN user_pseudo_id ELSE NULL END))
    AS new_users,
  COUNT(DISTINCT user_pseudo_id)
    - COUNT(
      DISTINCT (
        CASE WHEN user_type = "New user" THEN user_pseudo_id ELSE NULL END))
    AS returning_users,
  COUNT(
    DISTINCT (
      CASE WHEN engaged_session_event = 1 THEN user_pseudo_id ELSE NULL END))
    AS engaged_users,
  COUNT(event_name) AS event_count
FROM g-analytics-487213.bronze_us.ga4_events_sessionstart
WHERE FALSE
GROUP BY ALL;

-- Rebuild only recent partitions to keep the load idempotent and absorb late arrivals.
DELETE FROM `g-analytics-487213.silver_us.ga4_general_traffic`
WHERE event_date BETWEEN start_date AND end_date;

INSERT INTO `g-analytics-487213.silver_us.ga4_general_traffic`
  (
    event_date,
    event_name,
    device_category,
    device_operating_system,
    traffic_source,
    traffic_medium,
    traffic_campaign,
    traffic_term,
    country,
    region,
    city,
    total_sessions,
    engaged_sessions,
    total_users,
    new_users,
    returning_users,
    engaged_users,
    event_count)
SELECT
  event_date,
  event_name,
  device_category,
  device_operating_system,
  traffic_source,
  traffic_medium,
  traffic_campaign,
  traffic_term,
  country,
  region,
  city,
  COUNT(DISTINCT CONCAT(ga_session_id, '-', user_pseudo_id)) AS total_sessions,
  COUNT(
    DISTINCT (
      CASE
        WHEN engaged_session_event = 1
          THEN CONCAT(ga_session_id, '-', user_pseudo_id)
        ELSE NULL
        END)) AS engaged_sessions,
  COUNT(DISTINCT user_pseudo_id) AS total_users,
  COUNT(
    DISTINCT (
      CASE WHEN user_type = "New user" THEN user_pseudo_id ELSE NULL END))
    AS new_users,
  COUNT(DISTINCT user_pseudo_id)
    - COUNT(
      DISTINCT (
        CASE WHEN user_type = "New user" THEN user_pseudo_id ELSE NULL END))
    AS returning_users,
  COUNT(
    DISTINCT (
      CASE WHEN engaged_session_event = 1 THEN user_pseudo_id ELSE NULL END))
    AS engaged_users,
  COUNT(event_name) AS event_count
FROM g-analytics-487213.bronze_us.ga4_events_sessionstart
WHERE
  ga_session_id IS NOT NULL
  AND event_date BETWEEN start_date AND end_date
GROUP BY ALL
ORDER BY
  event_date DESC, total_sessions DESC, total_users DESC;
