"""Geracao de SQL controlado para BigQuery."""

from __future__ import annotations

from mcp_server.catalog import load_semantic_catalog
from mcp_server.models import MarketingQueryResult, PlannedQuery
from mcp_server.settings import load_bigquery_source_config


DATASET_TABLES: dict[str, list[str]] = {
    "ga4_silver": ["ga4_silver.ga4_general_traffic", "ga4_silver.ga4_ecommerce"],
    "ga4_bronze": ["ga4_bronze.ga4_events_ecommerce"],
    "google_ads": ["google_ads.p_ads_ad_group_ad_8784814486"],
    "facebook_ads_silver": ["facebook_ads_silver.fb_ad_insights"],
    "analytics_253977277": ["analytics_253977277.events_*"],
}

GA4_DATASETS = {"ga4_silver", "ga4_bronze", "analytics_253977277"}

DEFAULT_GA4_DATASET = "ga4_silver"

ALL_DEFAULT_DATASETS = ["ga4_silver", "google_ads", "facebook_ads_silver"]


def _channel_case() -> str:
    return """
    case
      when lower(coalesce(traffic_medium, '')) in ('cpc', 'ppc', 'paid', 'paid_search') then 'paid_search'
      when lower(coalesce(traffic_medium, '')) in ('paid_social', 'social_paid') then 'paid_social'
      when lower(coalesce(traffic_medium, '')) in ('organic', 'organic_search') then 'organic_search'
      when lower(coalesce(traffic_medium, '')) in ('email', 'newsletter') then 'email'
      when lower(coalesce(traffic_medium, '')) in ('referral') then 'referral'
      when lower(coalesce(traffic_source, '')) in ('direct', '(direct)') then 'direct'
      else coalesce(nullif(lower(traffic_medium), ''), nullif(lower(traffic_source), ''), 'unknown')
    end
    """.strip()


def _cte_ga4_silver(project_id: str) -> str:
    return f"""
    select
      event_date as date,
      {_channel_case()} as channel,
      'ga4' as platform,
      coalesce(nullif(traffic_campaign, ''), '(not set)') as campaign,
      sum(coalesce(total_sessions, 0)) as sessions,
      sum(coalesce(engaged_sessions, 0)) as engaged_sessions,
      sum(coalesce(total_users, 0)) as users,
      sum(coalesce(new_users, 0)) as new_users,
      cast(0 as int64) as conversions,
      cast(0 as int64) as orders,
      cast(0 as float64) as revenue,
      cast(0 as float64) as spend
    from `{project_id}.ga4_silver.ga4_general_traffic`
    group by 1, 2, 3, 4

    union all

    select
      event_date as date,
      {_channel_case()} as channel,
      'ga4' as platform,
      coalesce(nullif(traffic_campaign, ''), '(not set)') as campaign,
      cast(0 as int64) as sessions,
      cast(0 as int64) as engaged_sessions,
      sum(coalesce(purchasers, 0)) as users,
      cast(0 as int64) as new_users,
      sum(coalesce(transactions, 0)) as conversions,
      sum(coalesce(transactions, 0)) as orders,
      sum(coalesce(revenue, 0)) as revenue,
      cast(0 as float64) as spend
    from `{project_id}.ga4_silver.ga4_ecommerce`
    group by 1, 2, 3, 4""".strip()


def _cte_ga4_bronze(project_id: str) -> str:
    return f"""
    select
      date,
      {_channel_case()} as channel,
      'ga4' as platform,
      coalesce(nullif(traffic_campaign, ''), '(not set)') as campaign,
      cast(0 as int64) as sessions,
      cast(0 as int64) as engaged_sessions,
      count(distinct user_pseudo_id) as users,
      cast(0 as int64) as new_users,
      count(distinct transaction_id) as conversions,
      count(distinct transaction_id) as orders,
      sum(revenue) as revenue,
      cast(0 as float64) as spend
    from (
      select
        p.date,
        p.user_pseudo_id,
        p.transaction_id,
        coalesce(nullif(p.traffic_source, ''), s.traffic_source) as traffic_source,
        coalesce(nullif(p.traffic_medium, ''), s.traffic_medium) as traffic_medium,
        coalesce(nullif(p.traffic_campaign, ''), s.traffic_campaign) as traffic_campaign,
        p.revenue
      from (
        select
          event_date as date,
          user_pseudo_id,
          ga_session_id,
          transaction_id,
          max(traffic_source) as traffic_source,
          max(traffic_medium) as traffic_medium,
          max(traffic_campaign) as traffic_campaign,
          max(coalesce(purchase_revenue, 0)) as revenue
        from `{project_id}.ga4_bronze.ga4_events_ecommerce`
        where event_name = 'purchase'
          and transaction_id is not null
        group by 1, 2, 3, 4
      ) p
      left join `{project_id}.ga4_bronze.ga4_dim_session_traffic` s
        on  p.user_pseudo_id = s.user_pseudo_id
        and p.ga_session_id  = s.ga_session_id
    )
    group by 1, 2, 3, 4""".strip()


def _cte_google_ads(project_id: str) -> str:
    return f"""
    select
      segments_date as date,
      'paid_search' as channel,
      'google_ads' as platform,
      coalesce(nullif(campaign_name, ''), '(not set)') as campaign,
      cast(0 as int64) as sessions,
      cast(0 as int64) as engaged_sessions,
      cast(0 as int64) as users,
      cast(0 as int64) as new_users,
      sum(coalesce(metrics_conversions, 0)) as conversions,
      cast(0 as int64) as orders,
      sum(coalesce(metrics_conversions_value, 0)) as revenue,
      sum(coalesce(metrics_cost_micros, 0)) / 1000000.0 as spend
    from `{project_id}.google_ads.p_ads_ad_group_ad_8784814486`
    group by 1, 2, 3, 4""".strip()


def _cte_facebook_ads(project_id: str) -> str:
    return f"""
    select
      date_start as date,
      'paid_social' as channel,
      'facebook_ads' as platform,
      coalesce(nullif(campaign_name, ''), '(not set)') as campaign,
      cast(0 as int64) as sessions,
      cast(0 as int64) as engaged_sessions,
      sum(coalesce(reach, 0)) as users,
      cast(0 as int64) as new_users,
      sum(coalesce(purchase, 0)) as conversions,
      sum(coalesce(purchase, 0)) as orders,
      cast(0 as float64) as revenue,
      sum(coalesce(spend, 0)) as spend
    from `{project_id}.facebook_ads_silver.fb_ad_insights`
    group by 1, 2, 3, 4""".strip()


def _cte_analytics_raw(project_id: str) -> str:
    return f"""
    select
      date,
      {_channel_case()} as channel,
      'ga4' as platform,
      coalesce(nullif(traffic_campaign, ''), '(not set)') as campaign,
      cast(0 as int64) as sessions,
      cast(0 as int64) as engaged_sessions,
      count(distinct user_pseudo_id) as users,
      cast(0 as int64) as new_users,
      count(distinct transaction_id) as conversions,
      count(distinct transaction_id) as orders,
      sum(revenue) as revenue,
      cast(0 as float64) as spend
    from (
      select
        p.date,
        p.user_pseudo_id,
        p.transaction_id,
        coalesce(s.traffic_source, '') as traffic_source,
        coalesce(s.traffic_medium, '') as traffic_medium,
        coalesce(s.traffic_campaign, '') as traffic_campaign,
        p.revenue
      from (
        select
          parse_date('%Y%m%d', event_date) as date,
          user_pseudo_id,
          (select ep.value.int_value from unnest(event_params) ep where ep.key = 'ga_session_id' limit 1) as ga_session_id,
          ecommerce.transaction_id as transaction_id,
          max(coalesce(ecommerce.purchase_revenue, 0)) as revenue
        from `{project_id}.analytics_253977277.events_*`
        where event_name = 'purchase'
          and ecommerce.transaction_id is not null
        group by 1, 2, 3, 4
      ) p
      left join `{project_id}.ga4_bronze.ga4_dim_session_traffic` s
        on  p.user_pseudo_id = s.user_pseudo_id
        and p.ga_session_id  = s.ga_session_id
    )
    group by 1, 2, 3, 4""".strip()


CTE_BUILDERS: dict[str, callable] = {
    "ga4_silver": _cte_ga4_silver,
    "ga4_bronze": _cte_ga4_bronze,
    "google_ads": _cte_google_ads,
    "facebook_ads_silver": _cte_facebook_ads,
    "analytics_253977277": _cte_analytics_raw,
}


def _resolve_datasets(source_datasets: list[str]) -> list[str]:
    if not source_datasets:
        return ALL_DEFAULT_DATASETS.copy()

    requested = [ds for ds in source_datasets if ds in CTE_BUILDERS]
    ga4_requested = [ds for ds in requested if ds in GA4_DATASETS]

    if len(ga4_requested) > 1:
        raise ValueError(
            f"Datasets GA4 sao mutuamente exclusivos (mesmos dados em granularidades diferentes). "
            f"Escolha apenas um: {', '.join(ga4_requested)}. "
            f"Para comparar, execute uma consulta por dataset."
        )

    return requested


def _build_base_cte(
    project_id: str,
    datasets: list[str],
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, list[str]]:
    date_filters = []
    if start_date:
        date_filters.append(f"date >= date '{start_date}'")
    if end_date:
        date_filters.append(f"date <= date '{end_date}'")
    date_predicate = ""
    if date_filters:
        date_predicate = "\nwhere " + " and ".join(date_filters)

    sub_queries = [CTE_BUILDERS[ds](project_id) for ds in datasets]
    union_body = "\n\n    union all\n\n    ".join(sub_queries)

    source_tables = []
    for ds in datasets:
        source_tables.extend(DATASET_TABLES.get(ds, []))

    cte = f"""with base as (
  select *
  from (
    {union_body}
  ){date_predicate}
)"""
    return cte, source_tables


def build_marketing_query_sql(plan: PlannedQuery) -> str:
    catalog = load_semantic_catalog()
    source_config = load_bigquery_source_config()

    invalid_metrics = [metric for metric in plan.metrics if metric not in catalog.metrics]
    invalid_dimensions = [dimension for dimension in plan.dimensions if dimension not in catalog.dimensions]
    if invalid_metrics:
        raise ValueError(f"Metricas nao aprovadas: {', '.join(invalid_metrics)}")
    if invalid_dimensions:
        raise ValueError(f"Dimensoes nao aprovadas: {', '.join(invalid_dimensions)}")

    datasets = _resolve_datasets(plan.source_datasets)

    dimension_selects = list(plan.dimensions)
    metric_selects = [
        f"{catalog.metrics[metric].expression_hint} as {metric}"
        for metric in plan.metrics
    ]

    where_parts: list[str] = []
    for field, value in plan.filters.items():
        if field not in catalog.dimensions:
            continue
        where_parts.append(f"{field} = '{value}'")
    where_clause = ""
    if where_parts:
        where_clause = "\nwhere " + " and ".join(where_parts)

    group_by_clause = ""
    order_by_clause = ""
    if dimension_selects:
        positions = ", ".join(str(index) for index in range(1, len(dimension_selects) + 1))
        group_by_clause = f"\ngroup by {positions}"
        order_by_clause = f"\norder by {positions}"

    select_clause = ",\n  ".join(dimension_selects + metric_selects)
    limit = max(plan.limit, 1)

    cte, source_tables = _build_base_cte(
        project_id=source_config.project_id,
        datasets=datasets,
        start_date=plan.date_range.start_date if plan.date_range else None,
        end_date=plan.date_range.end_date if plan.date_range else None,
    )

    return f"""
{cte}
select
  {select_clause}
from base{where_clause}{group_by_clause}{order_by_clause}
limit {limit}
    """.strip()


def get_source_tables(plan: PlannedQuery) -> list[str]:
    datasets = _resolve_datasets(plan.source_datasets)
    tables = []
    for ds in datasets:
        tables.extend(DATASET_TABLES.get(ds, []))
    return tables


def empty_result(sql: str) -> MarketingQueryResult:
    return MarketingQueryResult(
        sql=sql,
        rows=[],
        row_count=0,
        source_tables=[],
    )
