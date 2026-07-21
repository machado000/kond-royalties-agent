"""Geracao de SQL controlado para Postgres."""

from __future__ import annotations

from mcp_server.catalog import SourceCatalog, load_semantic_catalog
from mcp_server.models import PlannedQuery, RoyaltyQueryResult
from mcp_server.settings import load_postgres_source_config


def _resolve_source(plan: PlannedQuery) -> tuple[str, SourceCatalog]:
    catalog = load_semantic_catalog()
    source_name = plan.source or catalog.default_source
    if source_name not in catalog.sources:
        raise ValueError(f"Fonte nao aprovada: {source_name}")
    return source_name, catalog.sources[source_name]


def build_royalty_query_sql(plan: PlannedQuery) -> str:
    source_name, source_catalog = _resolve_source(plan)
    postgres_sources = load_postgres_source_config()

    invalid_metrics = [m for m in plan.metrics if m not in source_catalog.metrics]
    invalid_dimensions = [d for d in plan.dimensions if d not in source_catalog.dimensions]
    if invalid_metrics:
        raise ValueError(f"Metricas nao aprovadas para a fonte '{source_name}': {', '.join(invalid_metrics)}")
    if invalid_dimensions:
        raise ValueError(f"Dimensoes nao aprovadas para a fonte '{source_name}': {', '.join(invalid_dimensions)}")

    dimension_selects = [
        f"{source_catalog.dimensions[d].expression_hint or d} as {d}" for d in plan.dimensions
    ]
    metric_selects = [
        f"{source_catalog.metrics[m].expression_hint} as {m}" for m in plan.metrics
    ]

    where_parts: list[str] = []
    period_dim = source_catalog.dimensions.get("period")
    if period_dim and plan.date_range:
        period_expr = period_dim.expression_hint or "period"
        if plan.date_range.start_date:
            where_parts.append(f"{period_expr} >= '{plan.date_range.start_date[:7]}'")
        if plan.date_range.end_date:
            where_parts.append(f"{period_expr} <= '{plan.date_range.end_date[:7]}'")

    for field, value in plan.filters.items():
        if field not in source_catalog.dimensions:
            continue
        field_expr = source_catalog.dimensions[field].expression_hint or field
        where_parts.append(f"lower({field_expr}) = lower('{value}')")

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

    qualified_table = postgres_sources.qualified_table_for(source_name)

    return f"""
select
  {select_clause}
from {qualified_table}{where_clause}{group_by_clause}{order_by_clause}
limit {limit}
    """.strip()


def get_source_tables(plan: PlannedQuery) -> list[str]:
    source_name, _ = _resolve_source(plan)
    postgres_sources = load_postgres_source_config()
    return [postgres_sources.qualified_table_for(source_name)]


def empty_result(sql: str) -> RoyaltyQueryResult:
    return RoyaltyQueryResult(
        sql=sql,
        rows=[],
        row_count=0,
        source_tables=[],
    )
