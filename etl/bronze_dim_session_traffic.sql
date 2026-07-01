-- BRONZE__DIM_SESSION_TRAFFIC_DAILY_INCREMENTAL
-- Runs after bronze_ga4_events_sessionstart.
-- Updates the session attribution dimension with new/changed sessions.

DECLARE lookback_days INT64 DEFAULT 3;
DECLARE run_date DATE DEFAULT CURRENT_DATE(); -- use on manual runs
-- DECLARE run_date DATE DEFAULT IFNULL(@run_date, CURRENT_DATE()); -- use on scheduled runs
DECLARE start_date DATE DEFAULT DATE_SUB(run_date, INTERVAL lookback_days DAY);
DECLARE end_date DATE DEFAULT DATE_SUB(run_date, INTERVAL 1 DAY);

MERGE `g-analytics-487213.bronze_us.ga4_dim_session_traffic` AS dim
USING (
  SELECT
    user_pseudo_id,
    ga_session_id,
    MAX(traffic_source)   AS traffic_source,
    MAX(traffic_medium)   AS traffic_medium,
    MAX(traffic_campaign) AS traffic_campaign,
    MAX(traffic_term)     AS traffic_term
  FROM `g-analytics-487213.bronze_us.ga4_events_sessionstart`
  WHERE event_date BETWEEN start_date AND end_date
    AND traffic_medium IS NOT NULL
    AND traffic_medium != ''
  GROUP BY 1, 2
) src
ON  dim.user_pseudo_id = src.user_pseudo_id
AND dim.ga_session_id  = src.ga_session_id
WHEN MATCHED THEN UPDATE SET
  dim.traffic_source   = src.traffic_source,
  dim.traffic_medium   = src.traffic_medium,
  dim.traffic_campaign = src.traffic_campaign,
  dim.traffic_term     = src.traffic_term
WHEN NOT MATCHED THEN INSERT (
  user_pseudo_id, ga_session_id,
  traffic_source, traffic_medium, traffic_campaign, traffic_term
) VALUES (
  src.user_pseudo_id, src.ga_session_id,
  src.traffic_source, src.traffic_medium, src.traffic_campaign, src.traffic_term
);
