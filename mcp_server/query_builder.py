"""Geracao de SQL controlado para Postgres."""

from __future__ import annotations

from mcp_server.catalog import load_semantic_catalog
from mcp_server.models import PlannedQuery, RoyaltyQueryResult
from mcp_server.settings import load_postgres_source_config


def build_royalty_query_sql(plan: PlannedQuery) -> str:
    catalog = load_semantic_catalog()
    source_config = load_postgres_source_config()

    invalid_metrics = [metric for metric in plan.metrics if metric not in catalog.metrics]
    invalid_dimensions = [dimension for dimension in plan.dimensions if dimension not in catalog.dimensions]
    if invalid_metrics:
        raise ValueError(f"Metricas nao aprovadas: {', '.join(invalid_metrics)}")
    if invalid_dimensions:
        raise ValueError(f"Dimensoes nao aprovadas: {', '.join(invalid_dimensions)}")

    dimension_selects = list(plan.dimensions)
    metric_selects = [
        f"{catalog.metrics[metric].expression_hint} as {metric}" for metric in plan.metrics
    ]

    where_parts: list[str] = []
    if plan.date_range and plan.date_range.start_date:
        where_parts.append(f"period >= '{plan.date_range.start_date[:7]}'")
    if plan.date_range and plan.date_range.end_date:
        where_parts.append(f"period <= '{plan.date_range.end_date[:7]}'")
    for field, value in plan.filters.items():
        if field not in catalog.dimensions:
            continue
        where_parts.append(f"lower({field}) = lower('{value}')")
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

    return f"""
select
  {select_clause}
from {source_config.qualified_table}{where_clause}{group_by_clause}{order_by_clause}
limit {limit}
    """.strip()


def get_source_tables(plan: PlannedQuery) -> list[str]:
    source_config = load_postgres_source_config()
    return [source_config.qualified_table]


def empty_result(sql: str) -> RoyaltyQueryResult:
    return RoyaltyQueryResult(
        sql=sql,
        rows=[],
        row_count=0,
        source_tables=[],
    )
