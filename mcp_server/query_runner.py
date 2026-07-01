"""Execucao controlada de consultas de marketing."""

from __future__ import annotations

from mcp_server.bigquery import create_bigquery_client
from mcp_server.models import MarketingQueryRequest, MarketingQueryResult, PlannedQuery
from mcp_server.planner import plan_marketing_query
from mcp_server.query_builder import build_marketing_query_sql, get_source_tables
from mcp_server.settings import load_app_settings


def run_planned_query(plan: PlannedQuery) -> MarketingQueryResult:
    sql = build_marketing_query_sql(plan)
    client = create_bigquery_client(load_app_settings())
    query_job = client.query(sql)
    rows = [dict(row.items()) for row in query_job.result()]
    return MarketingQueryResult(
        sql=sql,
        rows=rows,
        row_count=len(rows),
        source_tables=get_source_tables(plan),
    )


def run_marketing_query(request: MarketingQueryRequest) -> tuple[PlannedQuery, MarketingQueryResult]:
    plan = plan_marketing_query(request)
    result = run_planned_query(plan)
    return plan, result
