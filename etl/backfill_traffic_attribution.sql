-- BACKFILL_TRAFFIC_ATTRIBUTION
-- Preenche traffic_source, traffic_medium, traffic_campaign, traffic_term
-- nas tabelas fato usando ga4_events_sessionstart como dimensao de sessao.
--
-- Chave de join: (user_pseudo_id, ga_session_id)
-- Cobertura esperada: ~81% das sessoes tem medium preenchido no sessionstart.
-- Apenas preenche onde traffic_medium esta vazio (nao sobrescreve dados existentes).
--
-- Executar uma vez para backfill. Depois incluir na rotina diaria.

DECLARE start_date DATE DEFAULT DATE '2024-04-10';
DECLARE end_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY);

-- 1. Criar/recriar dimensao de sessao (deduplicada por user_pseudo_id + ga_session_id)
DROP TABLE IF EXISTS `g-analytics-487213.bronze_us.ga4_dim_session_traffic`;
CREATE TABLE `g-analytics-487213.bronze_us.ga4_dim_session_traffic`
AS
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
GROUP BY 1, 2;

-- 2. Atualizar ga4_events_ecommerce
MERGE `g-analytics-487213.bronze_us.ga4_events_ecommerce` AS fact
USING `g-analytics-487213.bronze_us.ga4_dim_session_traffic` AS dim
ON  fact.user_pseudo_id = dim.user_pseudo_id
AND fact.ga_session_id  = dim.ga_session_id
WHEN MATCHED
  AND fact.event_date BETWEEN start_date AND end_date
  AND (fact.traffic_medium IS NULL OR fact.traffic_medium = '')
THEN UPDATE SET
  fact.traffic_source   = dim.traffic_source,
  fact.traffic_medium   = dim.traffic_medium,
  fact.traffic_campaign = dim.traffic_campaign,
  fact.traffic_term     = dim.traffic_term;

-- 3. Atualizar ga4_events_click
MERGE `g-analytics-487213.bronze_us.ga4_events_click` AS fact
USING `g-analytics-487213.bronze_us.ga4_dim_session_traffic` AS dim
ON  fact.user_pseudo_id = dim.user_pseudo_id
AND fact.ga_session_id  = dim.ga_session_id
WHEN MATCHED
  AND fact.event_date BETWEEN start_date AND end_date
  AND (fact.traffic_medium IS NULL OR fact.traffic_medium = '')
THEN UPDATE SET
  fact.traffic_source   = dim.traffic_source,
  fact.traffic_medium   = dim.traffic_medium,
  fact.traffic_campaign = dim.traffic_campaign,
  fact.traffic_term     = dim.traffic_term;

-- 4. Atualizar ga4_events_pageview
MERGE `g-analytics-487213.bronze_us.ga4_events_pageview` AS fact
USING `g-analytics-487213.bronze_us.ga4_dim_session_traffic` AS dim
ON  fact.user_pseudo_id = dim.user_pseudo_id
AND fact.ga_session_id  = dim.ga_session_id
WHEN MATCHED
  AND fact.event_date BETWEEN start_date AND end_date
  AND (fact.traffic_medium IS NULL OR fact.traffic_medium = '')
THEN UPDATE SET
  fact.traffic_source   = dim.traffic_source,
  fact.traffic_medium   = dim.traffic_medium,
  fact.traffic_campaign = dim.traffic_campaign,
  fact.traffic_term     = dim.traffic_term;

-- 5. Atualizar ga4_events_submit
MERGE `g-analytics-487213.bronze_us.ga4_events_submit` AS fact
USING `g-analytics-487213.bronze_us.ga4_dim_session_traffic` AS dim
ON  fact.user_pseudo_id = dim.user_pseudo_id
AND fact.ga_session_id  = dim.ga_session_id
WHEN MATCHED
  AND fact.event_date BETWEEN start_date AND end_date
  AND (fact.traffic_medium IS NULL OR fact.traffic_medium = '')
THEN UPDATE SET
  fact.traffic_source   = dim.traffic_source,
  fact.traffic_medium   = dim.traffic_medium,
  fact.traffic_campaign = dim.traffic_campaign,
  fact.traffic_term     = dim.traffic_term;